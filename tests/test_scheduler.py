import unittest
from datetime import datetime

from greetings_bot.scheduler import is_greeting_due
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


if __name__ == "__main__":
    unittest.main()
