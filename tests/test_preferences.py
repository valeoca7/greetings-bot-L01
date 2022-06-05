import unittest

from greetings_bot.preferences import validate_greeting_time


class GreetingTimeTest(unittest.TestCase):
    def test_accepts_24_hour_time(self):
        self.assertEqual(validate_greeting_time(" 07:30 "), "07:30")
        self.assertEqual(validate_greeting_time("23:59"), "23:59")

    def test_rejects_invalid_time(self):
        for value in ("7:30", "24:00", "12:60", "evening"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_greeting_time(value)


if __name__ == "__main__":
    unittest.main()
