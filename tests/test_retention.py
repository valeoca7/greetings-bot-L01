import unittest

from greetings_bot.retention import RetentionPolicy, retention_from_env


class RetentionPolicyTest(unittest.TestCase):
    def test_uses_conservative_defaults(self):
        self.assertEqual(retention_from_env({}), RetentionPolicy(90, 14))

    def test_reads_bounded_retention_settings(self):
        policy = retention_from_env(
            {
                "DELIVERY_HISTORY_DAYS": "120",
                "DELIVERY_RECEIPT_DAYS": "7",
            }
        )

        self.assertEqual(policy, RetentionPolicy(120, 7))

    def test_rejects_unbounded_retention(self):
        for environ in (
            {"DELIVERY_HISTORY_DAYS": "1000"},
            {"DELIVERY_RECEIPT_DAYS": "0"},
            {"DELIVERY_HISTORY_DAYS": "forever"},
        ):
            with self.subTest(environ=environ):
                with self.assertRaises(ValueError):
                    retention_from_env(environ)


if __name__ == "__main__":
    unittest.main()
