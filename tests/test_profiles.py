import unittest

from greetings_bot.profiles import format_profile
from greetings_bot.users import User


class ProfileTest(unittest.TestCase):
    def test_formats_an_enabled_user(self):
        user = User(telegram_id=42, chat_id=42, first_name="Mira")

        profile = format_profile(user)

        self.assertEqual(
            profile,
            "Name: Mira\nTelegram ID: 42\nLanguage: en\n"
            "Greeting time: 09:00\nGreeting days: mon, tue, wed, thu, fri, sat, sun\n"
            "Quiet hours: off\nDaily digest: off\nTimezone: UTC\nGreetings: on",
        )

    def test_formats_a_disabled_user(self):
        user = User(
            telegram_id=42,
            chat_id=42,
            first_name="Mira",
            enabled=False,
        )

        self.assertIn("Greetings: off", format_profile(user))

    def test_formats_quiet_hours(self):
        user = User(
            telegram_id=42,
            chat_id=42,
            first_name="Mira",
            quiet_start="22:00",
            quiet_end="07:00",
        )

        self.assertIn("Quiet hours: 22:00-07:00", format_profile(user))


if __name__ == "__main__":
    unittest.main()
