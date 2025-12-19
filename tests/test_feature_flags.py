import unittest

from greetings_bot.feature_flags import FeatureFlags, feature_flags_from_env


class FeatureFlagsTest(unittest.TestCase):
    def test_uses_explicit_defaults(self):
        flags = feature_flags_from_env({})

        self.assertFalse(flags.enabled("information_requests"))
        self.assertTrue(flags.enabled("greeting_previews"))
        self.assertTrue(flags.enabled("weather_summaries"))

    def test_reads_boolean_environment_values(self):
        flags = feature_flags_from_env(
            {
                "INFO_REQUESTS_ENABLED": " TRUE ",
                "GREETING_PREVIEWS_ENABLED": "false",
            }
        )

        self.assertTrue(flags.enabled("information_requests"))
        self.assertFalse(flags.enabled("greeting_previews"))

    def test_rejects_ambiguous_values(self):
        with self.assertRaisesRegex(ValueError, "WEATHER_SUMMARIES_ENABLED"):
            feature_flags_from_env({"WEATHER_SUMMARIES_ENABLED": "sometimes"})

    def test_returns_an_allowlisted_public_snapshot(self):
        snapshot = feature_flags_from_env({}).public_snapshot()

        self.assertEqual(
            snapshot,
            (
                ("information_requests", False),
                ("greeting_previews", True),
                ("weather_summaries", True),
            ),
        )

    def test_rejects_incomplete_or_unknown_flag_sets(self):
        with self.assertRaises(ValueError):
            FeatureFlags({"information_requests": False})
        with self.assertRaises(KeyError):
            feature_flags_from_env({}).enabled("private_mode")


if __name__ == "__main__":
    unittest.main()
