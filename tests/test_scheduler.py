import unittest
from datetime import datetime

from greetings_bot.scheduler import build_greeting_replies, due_users, is_greeting_due
from greetings_bot.telegram import Reply
from greetings_bot.users import User


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


if __name__ == "__main__":
    unittest.main()
