import unittest

from greetings_bot.preferences import (
    set_first_name,
    set_greeting_days,
    set_greeting_time,
    set_quiet_hours,
    set_timezone,
    validate_greeting_time,
)
from greetings_bot.users import User


class GreetingTimeTest(unittest.TestCase):
    def test_accepts_24_hour_time(self):
        self.assertEqual(validate_greeting_time(" 07:30 "), "07:30")
        self.assertEqual(validate_greeting_time("23:59"), "23:59")

    def test_rejects_invalid_time(self):
        for value in ("7:30", "24:00", "12:60", "evening"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_greeting_time(value)

    def test_updates_an_immutable_user(self):
        user = User(telegram_id=42, chat_id=42, first_name="Mira")

        updated = set_greeting_time(user, "18:30")

        self.assertEqual(updated.greeting_time, "18:30")
        self.assertEqual(user.greeting_time, "09:00")

    def test_updates_greeting_name(self):
        user = User(telegram_id=42, chat_id=42, first_name="Mira")

        updated = set_first_name(user, " Mira Jane ")

        self.assertEqual(updated.first_name, "Mira Jane")

    def test_rejects_long_greeting_name(self):
        user = User(telegram_id=42, chat_id=42, first_name="Mira")

        with self.assertRaisesRegex(ValueError, "too long"):
            set_first_name(user, "x" * 41)

    def test_updates_timezone(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        updated = set_timezone(user, "America/Toronto")

        self.assertEqual("America/Toronto", updated.timezone)

    def test_sets_quiet_hours(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        updated = set_quiet_hours(user, "22:00", "07:00")

        self.assertEqual("22:00", updated.quiet_start)
        self.assertEqual("07:00", updated.quiet_end)

    def test_rejects_empty_quiet_window(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        with self.assertRaises(ValueError):
            set_quiet_hours(user, "08:00", "08:00")

    def test_sets_selected_greeting_days_in_week_order(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        updated = set_greeting_days(user, ("friday", "mon", "wed"))

        self.assertEqual(updated.greeting_days, ("mon", "wed", "fri"))

    def test_accepts_weekday_and_daily_shortcuts(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        self.assertEqual(
            set_greeting_days(user, ("weekdays",)).greeting_days,
            ("mon", "tue", "wed", "thu", "fri"),
        )
        self.assertEqual(len(set_greeting_days(user, ("daily",)).greeting_days), 7)

    def test_rejects_unknown_or_empty_greeting_days(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        for values in ((), ("funday",)):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    set_greeting_days(user, values)


if __name__ == "__main__":
    unittest.main()
