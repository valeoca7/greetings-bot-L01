import unittest

from greetings_bot.bedrock_information import BedrockInformationProvider
from greetings_bot.information_runtime import (
    DEFAULT_BEDROCK_MODEL_ID,
    information_requests_enabled,
    information_service_from_env,
    information_weekly_limit,
)


class InformationRuntimeTest(unittest.TestCase):
    def test_information_requests_are_disabled_by_default(self):
        self.assertFalse(information_requests_enabled({}))

    def test_enables_information_requests_explicitly(self):
        self.assertTrue(
            information_requests_enabled({"INFO_REQUESTS_ENABLED": "true"})
        )

    def test_rejects_ambiguous_feature_flag(self):
        with self.assertRaises(ValueError):
            information_requests_enabled({"INFO_REQUESTS_ENABLED": "sometimes"})

    def test_does_not_build_a_client_when_feature_is_disabled(self):
        self.assertIsNone(information_service_from_env({}, object()))

    def test_builds_a_service_with_the_default_model(self):
        client = object()

        service = information_service_from_env(
            {"INFO_REQUESTS_ENABLED": "true"}, client
        )

        self.assertIsInstance(service.provider, BedrockInformationProvider)
        self.assertIs(service.provider.client, client)
        self.assertEqual(service.provider.model_id, DEFAULT_BEDROCK_MODEL_ID)

    def test_accepts_a_configured_model(self):
        service = information_service_from_env(
            {
                "INFO_REQUESTS_ENABLED": "true",
                "BEDROCK_MODEL_ID": "amazon.example-v1",
            },
            object(),
        )

        self.assertEqual(service.provider.model_id, "amazon.example-v1")

    def test_rejects_a_blank_model(self):
        with self.assertRaises(ValueError):
            information_service_from_env(
                {
                    "INFO_REQUESTS_ENABLED": "true",
                    "BEDROCK_MODEL_ID": " ",
                },
                object(),
            )

    def test_reads_the_weekly_limit(self):
        self.assertEqual(information_weekly_limit({}), 5)
        self.assertEqual(
            information_weekly_limit({"INFO_WEEKLY_LIMIT": "9"}), 9
        )

    def test_rejects_an_invalid_weekly_limit(self):
        for value in ("0", "-1", "many"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    information_weekly_limit({"INFO_WEEKLY_LIMIT": value})


if __name__ == "__main__":
    unittest.main()
