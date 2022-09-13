import unittest

from greetings_bot.timezones import validate_timezone


class TimezoneTest(unittest.TestCase):
    def test_accepts_an_iana_timezone(self):
        self.assertEqual("America/Vancouver", validate_timezone(" America/Vancouver "))

    def test_rejects_an_unknown_timezone(self):
        with self.assertRaises(ValueError):
            validate_timezone("Moon/Base")


if __name__ == "__main__":
    unittest.main()
