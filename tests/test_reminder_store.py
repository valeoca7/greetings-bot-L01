import unittest
from datetime import datetime, timezone

from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import Reminder


def reminder(owner_id=42, reminder_id="abcd1234", status="pending"):
    return Reminder(
        reminder_id, owner_id, owner_id, "Call home",
        datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
        datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        status,
    )


class InMemoryReminderRepositoryTest(unittest.TestCase):
    def test_saves_owned_reminder(self):
        reminders = InMemoryReminderRepository()
        value = reminder()

        reminders.save(value)

        self.assertEqual(reminders.get(42, "abcd1234"), value)
        self.assertIsNone(reminders.get(7, "abcd1234"))

    def test_lists_only_owner_reminders_by_due_time(self):
        reminders = InMemoryReminderRepository()
        later = reminder(reminder_id="later")
        earlier = Reminder(
            "earlier", 42, 42, "First",
            datetime(2023, 3, 31, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )
        reminders.save(later)
        reminders.save(earlier)
        reminders.save(reminder(owner_id=7, reminder_id="other"))

        self.assertEqual(reminders.all_for(42), [earlier, later])

    def test_selects_bounded_pending_due_reminders(self):
        reminders = InMemoryReminderRepository()
        reminders.save(reminder(reminder_id="due"))
        reminders.save(reminder(reminder_id="sent", status="sent"))
        future = Reminder(
            "future", 7, 7, "Later",
            datetime(2023, 4, 2, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )
        reminders.save(future)

        due = reminders.due_before(
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc), 1
        )

        self.assertEqual([value.id for value in due], ["due"])


if __name__ == "__main__":
    unittest.main()
