import unittest

from greetings_bot.throughput import ThroughputPolicy, throughput_from_env


class ThroughputPolicyTest(unittest.TestCase):
    def test_uses_safe_defaults(self):
        self.assertEqual(throughput_from_env({}), ThroughputPolicy(100, 1000, 100))

    def test_reads_bounded_limits(self):
        policy = throughput_from_env(
            {
                "DISPATCH_BATCH_SIZE": "40",
                "DELIVERY_QUEUE_HIGH_WATERMARK": "600",
                "PROFILE_SCAN_PAGE_SIZE": "75",
            }
        )

        self.assertEqual(policy, ThroughputPolicy(40, 600, 75))

    def test_rejects_invalid_limits(self):
        for environ in (
            {"DISPATCH_BATCH_SIZE": "0"},
            {"DISPATCH_BATCH_SIZE": "501"},
            {"DELIVERY_QUEUE_HIGH_WATERMARK": "9"},
            {"DELIVERY_QUEUE_HIGH_WATERMARK": "many"},
            {"PROFILE_SCAN_PAGE_SIZE": "9"},
        ):
            with self.subTest(environ=environ):
                with self.assertRaisesRegex(ValueError, "throughput"):
                    throughput_from_env(environ)


if __name__ == "__main__":
    unittest.main()
