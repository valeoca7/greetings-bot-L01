import unittest

from greetings_bot.webhook_auth import TelegramWebhookAuthorizer


class TelegramWebhookAuthorizerTest(unittest.TestCase):
    def test_accepts_the_matching_secret_header(self):
        authorizer = TelegramWebhookAuthorizer("local-secret_123")

        self.assertTrue(
            authorizer.authorize(
                {"x-telegram-bot-api-secret-token": "local-secret_123"}
            )
        )

    def test_rejects_missing_or_wrong_secrets(self):
        authorizer = TelegramWebhookAuthorizer("local-secret_123")

        self.assertFalse(authorizer.authorize({}))
        self.assertFalse(
            authorizer.authorize(
                {"x-telegram-bot-api-secret-token": "another-secret1"}
            )
        )

    def test_rejects_weak_or_unsupported_configured_secrets(self):
        for secret in ("short", "spaces are private", "x" * 257):
            with self.subTest(secret=secret):
                with self.assertRaisesRegex(ValueError, "webhook secret"):
                    TelegramWebhookAuthorizer(secret)


if __name__ == "__main__":
    unittest.main()
