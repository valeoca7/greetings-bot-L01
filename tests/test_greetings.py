import unittest
from datetime import datetime, timezone

from greetings_bot.greeting_templates import (
    GreetingTemplate,
    GreetingTemplateCatalog,
)
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

    def test_uses_the_selected_scheduled_greeting_style(self):
        user = User(
            42, 42, "Mira", greeting_template_category="cheerful"
        )

        self.assertEqual(
            format_scheduled_greeting(user),
            "Hope your day starts well, Mira!",
        )

    def test_supplies_local_date_values_to_the_renderer(self):
        user = User(42, 42, "Mira", timezone="America/Vancouver")
        templates = GreetingTemplateCatalog(
            (
                GreetingTemplate(
                    "friendly", "en", "{weekday}, {date}: hello {name}!"
                ),
            )
        )

        text = format_scheduled_greeting(
            user,
            datetime(2025, 10, 28, 2, 0, tzinfo=timezone.utc),
            templates,
        )

        self.assertEqual(text, "Monday, 2025-10-27: hello Mira!")


if __name__ == "__main__":
    unittest.main()
