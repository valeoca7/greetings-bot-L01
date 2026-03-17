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
        self.assertEqual(config.dispatch_batch_size, 100)
        self.assertEqual(config.queue_high_watermark, 1000)
        self.assertEqual(config.usage_budgets[0], ("weather_calls", 500))
        self.assertEqual(config.supported_locales, ("en", "uk"))
        self.assertEqual(config.fallback_locale, "en")
        self.assertEqual(
            config.template_categories, ("friendly", "brief", "cheerful")
        )
        self.assertEqual(config.template_variables, ("name", "weekday", "date"))
        self.assertEqual(
            config.feature_flags,
            (
                ("information_requests", False),
                ("greeting_previews", True),
                ("weather_summaries", True),
            ),
        )
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
                "DISPATCH_BATCH_SIZE": "40",
                "DELIVERY_QUEUE_HIGH_WATERMARK": "600",
                "WEATHER_DAILY_BUDGET": "80",
                "INFORMATION_DAILY_BUDGET": "20",
                "QUEUE_DAILY_BUDGET": "900",
            }
        )

        self.assertTrue(config.information_enabled)
        self.assertEqual(config.information_weekly_limit, 8)
        self.assertEqual(config.weather_cache_minutes, 30)
        self.assertEqual(config.weather_stale_hours, 12)
        self.assertTrue(config.delivery_admin_configured)
        self.assertEqual(config.delivery_history_days, 120)
        self.assertEqual(config.delivery_receipt_days, 7)
        self.assertEqual(config.dispatch_batch_size, 40)
        self.assertEqual(config.queue_high_watermark, 600)
        self.assertEqual(
            config.usage_budgets,
            (
                ("weather_calls", 80),
                ("information_requests", 20),
                ("queued_messages", 900),
            ),
        )
        self.assertNotIn("secret", repr(config))

    def test_rejects_invalid_numeric_configuration(self):
        with self.assertRaises(ValueError):
            dashboard_config_from_env({"WEATHER_MAX_CALLS": "many"})


if __name__ == "__main__":
    unittest.main()
