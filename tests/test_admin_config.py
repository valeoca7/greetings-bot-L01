import unittest

from greetings_bot.admin_config import dashboard_config_from_env


class AdminConfigTest(unittest.TestCase):
    def test_reads_safe_runtime_defaults(self):
        config = dashboard_config_from_env({})

        self.assertFalse(config.information_enabled)
        self.assertEqual(config.information_weekly_limit, 5)
        self.assertEqual(config.bedrock_model, "amazon.titan-text-lite-v1")
        self.assertEqual(config.weather_max_calls, 20)
        self.assertEqual(config.delivery_history_days, 90)
        self.assertEqual(config.delivery_receipt_days, 14)
        self.assertFalse(config.delivery_admin_configured)

    def test_reads_selected_runtime_configuration(self):
        config = dashboard_config_from_env(
            {
                "INFO_REQUESTS_ENABLED": "true",
                "INFO_WEEKLY_LIMIT": "8",
                "BEDROCK_MODEL_ID": "amazon.example-v1",
                "WEATHER_MAX_CALLS": "15",
                "WEATHER_CACHE_MINUTES": "30",
                "WEATHER_STALE_HOURS": "12",
                "DELIVERY_QUEUE_URL": "secret-url",
                "DELIVERY_DLQ_URL": "secret-dlq-url",
                "DELIVERY_QUEUE_ARN": "secret-arn",
                "DELIVERY_DLQ_ARN": "secret-dlq-arn",
                "ADMIN_API_TOKEN": "do-not-expose",
                "DELIVERY_HISTORY_DAYS": "120",
                "DELIVERY_RECEIPT_DAYS": "7",
            }
        )

        self.assertTrue(config.information_enabled)
        self.assertEqual(config.information_weekly_limit, 8)
        self.assertEqual(config.weather_cache_minutes, 30)
        self.assertEqual(config.weather_stale_hours, 12)
        self.assertTrue(config.delivery_admin_configured)
        self.assertEqual(config.delivery_history_days, 120)
        self.assertEqual(config.delivery_receipt_days, 7)
        self.assertNotIn("secret", repr(config))

    def test_rejects_invalid_numeric_configuration(self):
        with self.assertRaises(ValueError):
            dashboard_config_from_env({"WEATHER_MAX_CALLS": "many"})


if __name__ == "__main__":
    unittest.main()
