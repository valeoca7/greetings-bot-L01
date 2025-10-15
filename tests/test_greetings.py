import unittest

from greetings_bot.greetings import format_greeting, format_scheduled_greeting
from greetings_bot.telegram import TelegramUser
from greetings_bot.users import User


class GreetingTest(unittest.TestCase):
    def test_uses_the_first_name(self):
        user = TelegramUser(id=42, first_name="Mira")

        self.assertEqual(format_greeting(user), "Hello, Mira!")

    def test_handles_a_blank_first_name(self):
        user = TelegramUser(id=42, first_name="  ")

        self.assertEqual(format_greeting(user), "Hello!")

    def test_formats_a_scheduled_greeting(self):
        user = User(telegram_id=8, chat_id=8, first_name="Mira")

        self.assertEqual("Good day, Mira!", format_scheduled_greeting(user))

    def test_formats_ukrainian_greetings(self):
        telegram_user = TelegramUser(id=42, first_name="Міра")
        saved_user = User(
            telegram_id=42, chat_id=42, first_name="Міра", locale="uk"
        )

        self.assertEqual(
            format_greeting(telegram_user, locale="uk"), "Вітаю, Міра!"
        )
        self.assertEqual(
            format_scheduled_greeting(saved_user), "Добрий день, Міра!"
        )


if __name__ == "__main__":
    unittest.main()
