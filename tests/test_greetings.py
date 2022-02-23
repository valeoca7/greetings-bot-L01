import unittest

from greetings_bot.greetings import format_greeting
from greetings_bot.telegram import TelegramUser


class GreetingTest(unittest.TestCase):
    def test_uses_the_first_name(self):
        user = TelegramUser(id=42, first_name="Mira")

        self.assertEqual(format_greeting(user), "Hello, Mira!")

    def test_handles_a_blank_first_name(self):
        user = TelegramUser(id=42, first_name="  ")

        self.assertEqual(format_greeting(user), "Hello!")


if __name__ == "__main__":
    unittest.main()
