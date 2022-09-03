import unittest
from datetime import datetime

from greetings_bot.clock import FixedClock
from greetings_bot.scheduler import (
    GreetingDispatcher,
    build_greeting_replies,
    due_users,
    is_greeting_due,
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

    def test_skips_disabled_users(self):
        user = User(
            telegram_id=3,
            chat_id=3,
            first_name="Lee",
            greeting_time="09:00",
            enabled=False,
        )

        self.assertEqual([], due_users([user], datetime(2022, 8, 5, 9, 0)))

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


if __name__ == "__main__":
    unittest.main()
