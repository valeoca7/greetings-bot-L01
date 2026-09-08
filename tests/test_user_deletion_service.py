import unittest
from datetime import datetime, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import Reminder
from greetings_bot.user_data_cleanup import CleanupBatch
from greetings_bot.user_deletion_service import (
    UserDeletionError,
    UserDeletionService,
)
from greetings_bot.user_deletion_store import (
    InMemoryDeletionRequestRepository,
)
from greetings_bot.users import InMemoryUserRepository, User


class UserDeletionServiceTest(unittest.TestCase):
    def setUp(self):
        self.users = InMemoryUserRepository()
        self.users.save(User(42, 4200, "Mira"))
        self.requests = InMemoryDeletionRequestRepository()
        self.clock = FixedClock(
            datetime(2025, 8, 25, 3, 0, tzinfo=timezone.utc)
        )

    def service(self, token="deletion-token-number-one"):
        return UserDeletionService(
            self.users,
            self.requests,
            self.clock,
            lambda: token,
        )

    def test_issues_a_token_but_persists_only_its_digest(self):
        token = self.service().request(42)

        stored = self.requests.get(42)
        self.assertEqual(token, "deletion-token-number-one")
        self.assertNotEqual(stored.token_digest, token)

    def test_requires_an_existing_user(self):
        with self.assertRaises(UserDeletionError):
            self.service().request(7)

        self.assertIsNone(self.requests.get(7))

    def test_confirms_and_saves_the_matching_request(self):
        service = self.service()
        token = service.request(42)

        confirmed = service.confirm(42, token)

        self.assertEqual(confirmed.status, "confirmed")
        self.assertEqual(self.requests.get(42), confirmed)

    def test_a_replacement_invalidates_the_previous_token(self):
        first = self.service("first-deletion-token").request(42)
        service = self.service("second-deletion-token")
        second = service.request(42)

        with self.assertRaises(UserDeletionError):
            service.confirm(42, first)

        confirmed = service.confirm(42, second)
        self.assertEqual(confirmed.status, "confirmed")

    def test_executes_a_confirmed_cleanup_and_removes_one_time_schedules(self):
        class Cleaner:
            def erase_batch(self, telegram_id, limit=100):
                self.telegram_id = telegram_id
                return CleanupBatch(3, True)

        class Scheduler:
            def __init__(self):
                self.deleted = []

            def delete(self, reminder):
                self.deleted.append(reminder.id)

        reminders = InMemoryReminderRepository()
        one_time = Reminder(
            "once", 42, 4200, "Call home",
            self.clock.now(), self.clock.now(),
        )
        recurring = Reminder(
            "daily", 42, 4200, "Stretch",
            self.clock.now(), self.clock.now(), recurrence="daily",
        )
        reminders.save(one_time)
        reminders.save(recurring)
        cleaner = Cleaner()
        scheduler = Scheduler()
        service = UserDeletionService(
            self.users,
            self.requests,
            self.clock,
            lambda: "deletion-token-number-one",
            cleaner,
            reminders,
            scheduler,
        )
        token = service.request(42)
        service.confirm(42, token)

        completed = service.execute(42)

        self.assertEqual(completed.status, "completed")
        self.assertEqual(cleaner.telegram_id, 42)
        self.assertEqual(scheduler.deleted, ["once"])

    def test_leaves_request_confirmed_when_cleanup_needs_another_pass(self):
        class BusyCleaner:
            def erase_batch(self, telegram_id, limit=100):
                return CleanupBatch(100, False)

        service = UserDeletionService(
            self.users,
            self.requests,
            self.clock,
            lambda: "deletion-token-number-one",
            BusyCleaner(),
            InMemoryReminderRepository(),
            type("Scheduler", (), {"delete": lambda self, value: None})(),
        )
        token = service.request(42)
        service.confirm(42, token)

        with self.assertRaises(UserDeletionError):
            service.execute(42, max_batches=1)

        self.assertEqual(self.requests.get(42).status, "confirmed")

    def test_retries_an_interrupted_cleanup_until_it_is_complete(self):
        class InterruptedCleaner:
            def __init__(self):
                self.calls = 0

            def erase_batch(self, telegram_id, limit=100):
                self.calls += 1
                return CleanupBatch(1, self.calls > 1)

        class IdempotentScheduler:
            def __init__(self):
                self.deleted = set()

            def delete(self, reminder):
                self.deleted.add(reminder.id)

        reminders = InMemoryReminderRepository()
        reminders.save(
            Reminder(
                "once",
                42,
                4200,
                "Call home",
                self.clock.now(),
                self.clock.now(),
            )
        )
        cleaner = InterruptedCleaner()
        scheduler = IdempotentScheduler()
        service = UserDeletionService(
            self.users,
            self.requests,
            self.clock,
            lambda: "deletion-token-number-one",
            cleaner,
            reminders,
            scheduler,
        )
        token = service.request(42)
        service.confirm(42, token)

        with self.assertRaisesRegex(UserDeletionError, "another pass"):
            service.execute(42, max_batches=1)
        completed = service.execute(42, max_batches=1)

        self.assertEqual(completed.status, "completed")
        self.assertEqual(cleaner.calls, 2)
        self.assertEqual(scheduler.deleted, {"once"})


if __name__ == "__main__":
    unittest.main()
