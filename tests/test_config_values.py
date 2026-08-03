import unittest

from greetings_bot.config_values import (
    ConfigurationError,
    integer_value,
    nonblank_value,
)


class IntegerValueTest(unittest.TestCase):
    def test_reads_default_and_configured_values(self):
        self.assertEqual(integer_value({}, "BATCH_SIZE", 20), 20)
        self.assertEqual(integer_value({"BATCH_SIZE": "8"}, "BATCH_SIZE", 20), 8)

    def test_names_non_integer_settings_without_repeating_values(self):
        with self.assertRaisesRegex(ConfigurationError, "BATCH_SIZE must be an integer"):
            integer_value({"BATCH_SIZE": "private-value"}, "BATCH_SIZE", 20)

    def test_applies_optional_bounds(self):
        for value in ("0", "101"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ConfigurationError, "between 1 and 100"):
                    integer_value({"BATCH_SIZE": value}, "BATCH_SIZE", 20, 1, 100)


class NonblankValueTest(unittest.TestCase):
    def test_strips_a_configured_or_default_value(self):
        self.assertEqual(nonblank_value({"MODEL": " small "}, "MODEL"), "small")
        self.assertEqual(nonblank_value({}, "MODEL", "default"), "default")

    def test_rejects_missing_and_blank_values_by_name(self):
        for environ in ({}, {"MODEL": "  "}):
            with self.subTest(environ=environ):
                with self.assertRaisesRegex(ConfigurationError, "MODEL"):
                    nonblank_value(environ, "MODEL")


if __name__ == "__main__":
    unittest.main()
