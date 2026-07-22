import unittest

from greetings_bot.config_values import ConfigurationError, integer_value


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


if __name__ == "__main__":
    unittest.main()
