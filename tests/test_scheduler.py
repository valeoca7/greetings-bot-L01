import unittest
from datetime import date, datetime, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.deliveries import Delivery
from greetings_bot.scheduler import (
    GreetingDispatcher,
    build_greeting_replies,
    due_users,
    greeting_delivery,
    is_greeting_due,
    is_quiet_time,
)
from greetings_bot.telegram import Reply
from greetings_bot.users import InMemoryUserRepository, User


class GreetingScheduleTest(unittest.TestCase):
    def test_matches_greeting_minute(self):
        user = User(
            telegram_id=42,
            chat_id=42,
            first_name="Mira",
            greeting_time="18:30",
        )

        self.assertTrue(is_greeting_due(user, datetime(2022, 8, 1, 18, 30)))
        self.assertFalse(is_greeting_due(user, datetime(2022, 8, 1, 18, 31)))

    def test_selects_users_for_the_current_minute(self):
        early = User(telegram_id=1, chat_id=1, first_name="Mira", greeting_time="08:00")
        late = User(telegram_id=2, chat_id=2, first_name="Sam", greeting_time="18:30")

        self.assertEqual([late], due_users([early, late], datetime(2022, 8, 3, 18, 30)))

    def test_matches_each_users_local_time(self):
        west = User(8, 8, "West", greeting_time="09:00", timezone="America/Vancouver")
        east = User(9, 9, "East", greeting_time="12:00", timezone="America/Toronto")
        current = datetime(2022, 9, 29, 16, 0, tzinfo=timezone.utc)

        self.assertEqual([west, east], due_users([west, east], current))

    def test_skips_disabled_users(self):
        user = User(
            telegram_id=3,
            chat_id=3,
            first_name="Lee",
            greeting_time="09:00",
            enabled=False,
        )

        self.assertEqual([], due_users([user], datetime(2022, 8, 5, 9, 0)))

    def test_detects_overnight_quiet_hours(self):
        user = User(3, 3, "Lee", quiet_start="22:00", quiet_end="07:00")

        self.assertTrue(is_quiet_time(user, datetime(2022, 10, 12, 23, 0)))
        self.assertTrue(is_quiet_time(user, datetime(2022, 10, 13, 6, 59)))
        self.assertFalse(is_quiet_time(user, datetime(2022, 10, 13, 7, 0)))

    def test_skips_a_greeting_during_quiet_hours(self):
        user = User(
            3,
            3,
            "Lee",
            greeting_time="06:30",
            quiet_start="22:00",
            quiet_end="07:00",
        )

        self.assertEqual([], due_users([user], datetime(2022, 10, 12, 6, 30)))

    def test_builds_replies_for_due_users(self):
        user = User(telegram_id=4, chat_id=40, first_name="Jo")

        self.assertEqual(
            [Reply(chat_id=40, text="Good day, Jo!")],
            build_greeting_replies([user]),
        )

    def test_dispatches_due_users_from_repository(self):
        users = InMemoryUserRepository()
        users.save(User(telegram_id=5, chat_id=50, first_name="Kim", greeting_time="07:15"))
        clock = FixedClock(datetime(2022, 8, 17, 7, 15))

        replies = GreetingDispatcher(users, clock).dispatch()

        self.assertEqual([Reply(chat_id=50, text="Good day, Kim!")], replies)

    def test_logs_number_of_due_greetings(self):
        users = InMemoryUserRepository()
        clock = FixedClock(datetime(2022, 8, 25, 7, 15))

        with self.assertLogs("greetings_bot.scheduler", level="INFO") as logs:
            GreetingDispatcher(users, clock).dispatch()

        self.assertIn("dispatching 0 scheduled greetings", logs.output[0])

    def test_does_not_dispatch_twice_on_the_same_day(self):
        users = InMemoryUserRepository()
        users.save(User(telegram_id=6, chat_id=60, first_name="Ari", greeting_time="08:00"))
        dispatcher = GreetingDispatcher(
            users,
            FixedClock(datetime(2022, 8, 31, 8, 0)),
        )

        self.assertEqual(1, len(dispatcher.dispatch()))
        self.assertEqual([], dispatcher.dispatch())

    def test_dispatches_again_on_the_next_day(self):
        users = InMemoryUserRepository()
        users.save(User(telegram_id=7, chat_id=70, first_name="Noa", greeting_time="08:00"))
        clock = FixedClock(datetime(2022, 9, 1, 8, 0))
        dispatcher = GreetingDispatcher(users, clock)

        self.assertEqual(1, len(dispatcher.dispatch()))
        clock.current_time = datetime(2022, 9, 2, 8, 0)

        self.assertEqual(1, len(dispatcher.dispatch()))

    def test_does_not_repeat_during_fall_clock_change(self):
        users = InMemoryUserRepository()
        users.save(
            User(
                telegram_id=10,
                chat_id=10,
                first_name="Mira",
                greeting_time="01:30",
                timezone="America/Vancouver",
            )
        )
        clock = FixedClock(datetime(2022, 11, 6, 8, 30, tzinfo=timezone.utc))
        dispatcher = GreetingDispatcher(users, clock)

        self.assertEqual(1, len(dispatcher.dispatch()))
        clock.current_time = datetime(2022, 11, 6, 9, 30, tzinfo=timezone.utc)

        self.assertEqual([], dispatcher.dispatch())

    def test_limits_one_dispatch_batch(self):
        users = InMemoryUserRepository()
        users.save(User(1, 1, "Mira", greeting_time="08:00"))
        users.save(User(2, 2, "Leo", greeting_time="08:00"))
        dispatcher = GreetingDispatcher(
            users,
            FixedClock(datetime(2023, 1, 5, 8, 0)),
            max_batch=1,
        )

        self.assertEqual(len(dispatcher.dispatch()), 1)

    def test_rejects_empty_batch_limit(self):
        with self.assertRaisesRegex(ValueError, "max_batch"):
            GreetingDispatcher(
                InMemoryUserRepository(),
                FixedClock(datetime(2023, 1, 5, 8, 0)),
                max_batch=0,
            )

    def test_records_delivery_on_the_users_local_day(self):
        user = User(42, 42, "Mira", timezone="Asia/Tokyo")
        current = datetime(2023, 1, 8, 15, 30, tzinfo=timezone.utc)

        self.assertEqual(
            greeting_delivery(user, current),
            Delivery(42, date(2023, 1, 9)),
        )


if __name__ == "__main__":
    unittest.main()
