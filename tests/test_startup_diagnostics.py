import unittest

from greetings_bot.startup_diagnostics import startup_diagnostics_from_env


class StartupDiagnosticsTest(unittest.TestCase):
    def test_contains_only_feature_states_and_numeric_limits(self):
        values = startup_diagnostics_from_env(
            {
                "INFO_REQUESTS_ENABLED": "true",
                "INFO_WEEKLY_LIMIT": "7",
                "BEDROCK_MODEL_ID": "private-model",
                "TELEGRAM_BOT_TOKEN": "private-token",
                "USER_TABLE_NAME": "private-table",
                "DELIVERY_QUEUE_URL": "private-url",
                "WEATHER_MAX_CALLS": "12",
            }
        )

        self.assertTrue(values["information_requests"])
        self.assertEqual(values["information_weekly_limit"], 7)
        self.assertEqual(values["weather_max_calls"], 12)
        self.assertTrue(all(isinstance(value, (bool, int)) for value in values.values()))
        self.assertNotIn("private", repr(values))

    def test_names_invalid_settings_before_logging(self):
        with self.assertRaisesRegex(ValueError, "QUEUE_DAILY_BUDGET"):
            startup_diagnostics_from_env({"QUEUE_DAILY_BUDGET": "lots"})


if __name__ == "__main__":
    unittest.main()
