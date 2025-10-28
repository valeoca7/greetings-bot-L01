import unittest

from greetings_bot.preferences import (
    clear_weather_location,
    set_first_name,
    set_digest_mode,
    set_greeting_days,
    set_greeting_template_category,
    set_greeting_time,
    set_quiet_hours,
    set_locale,
    set_timezone,
    set_weather_location,
    set_weather_units,
    set_weather_summary,
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

    def test_updates_a_supported_locale(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        updated = set_locale(user, "uk-UA")

        self.assertEqual(updated.locale, "uk")

    def test_rejects_an_unsupported_locale(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        with self.assertRaises(ValueError):
            set_locale(user, "fr")

    def test_updates_a_supported_greeting_template_category(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        updated = set_greeting_template_category(user, " Cheerful ")

        self.assertEqual(updated.greeting_template_category, "cheerful")

    def test_rejects_an_unknown_greeting_template_category(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        with self.assertRaises(ValueError):
            set_greeting_template_category(user, "surprise")

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

    def test_sets_a_daily_digest(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        updated = set_digest_mode(user, "DAILY")

        self.assertEqual(updated.digest_mode, "daily")

    def test_rejects_unknown_digest_mode(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        with self.assertRaises(ValueError):
            set_digest_mode(user, "weekly")

    def test_sets_and_clears_weather_location(self):
        user = User(
            telegram_id=1,
            chat_id=1,
            first_name="Mira",
            weather_summary=True,
        )

        located = set_weather_location(user, "Vancouver", "49.2827", "-123.1207")

        self.assertEqual(located.weather_location.name, "Vancouver")
        self.assertEqual(located.weather_location.latitude, 49.2827)
        cleared = clear_weather_location(located)
        self.assertIsNone(cleared.weather_location)
        self.assertFalse(cleared.weather_summary)

    def test_rejects_invalid_weather_location(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        with self.assertRaisesRegex(ValueError, "invalid weather location"):
            set_weather_location(user, "Nowhere", "north", "west")

    def test_sets_weather_units(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        updated = set_weather_units(user, "IMPERIAL")

        self.assertEqual(updated.weather_units, "imperial")

    def test_rejects_unknown_weather_units(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        with self.assertRaises(ValueError):
            set_weather_units(user, "kelvin")

    def test_enables_and_disables_daily_weather(self):
        user = User(telegram_id=1, chat_id=1, first_name="Mira")

        enabled = set_weather_summary(user, True)
        disabled = set_weather_summary(enabled, False)

        self.assertTrue(enabled.weather_summary)
        self.assertEqual(enabled.digest_mode, "daily")
        self.assertFalse(disabled.weather_summary)


if __name__ == "__main__":
    unittest.main()
