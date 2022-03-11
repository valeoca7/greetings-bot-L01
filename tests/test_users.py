import unittest

from greetings_bot.users import User


class UserTest(unittest.TestCase):
    def test_keeps_telegram_profile(self):
        user = User(telegram_id=42, chat_id=84, first_name="Mira")

        self.assertEqual(user.telegram_id, 42)
        self.assertEqual(user.chat_id, 84)
        self.assertEqual(user.first_name, "Mira")


if __name__ == "__main__":
    unittest.main()
