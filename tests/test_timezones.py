import unittest
from datetime import datetime, timezone

from greetings_bot.timezones import user_local_time, validate_timezone
from greetings_bot.users import User


class TimezoneTest(unittest.TestCase):
    def test_accepts_an_iana_timezone(self):
        self.assertEqual("America/Vancouver", validate_timezone(" America/Vancouver "))

    def test_rejects_an_unknown_timezone(self):
        with self.assertRaises(ValueError):
            validate_timezone("Moon/Base")

    def test_converts_utc_time_for_a_user(self):
        user = User(1, 1, "Mira", timezone="America/Vancouver")
        current = datetime(2022, 9, 27, 16, 0, tzinfo=timezone.utc)

        self.assertEqual("09:00", user_local_time(user, current).strftime("%H:%M"))

    def test_uses_daylight_offset_after_spring_change(self):
        user = User(1, 1, "Mira", timezone="America/Vancouver")
        before = datetime(2022, 3, 13, 9, 30, tzinfo=timezone.utc)
        after = datetime(2022, 3, 13, 10, 30, tzinfo=timezone.utc)

        self.assertEqual("01:30", user_local_time(user, before).strftime("%H:%M"))
        self.assertEqual("03:30", user_local_time(user, after).strftime("%H:%M"))


if __name__ == "__main__":
    unittest.main()
