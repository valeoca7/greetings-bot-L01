import unittest

from greetings_bot.admin_api import AdminRequest
from greetings_bot.admin_auth import BearerTokenAuthorizer


class BearerTokenAuthorizerTest(unittest.TestCase):
    def test_accepts_the_configured_bearer_token(self):
        request = AdminRequest(
            "GET",
            "/admin/health",
            {"authorization": "Bearer a-long-local-admin-token"},
        )

        self.assertTrue(
            BearerTokenAuthorizer("a-long-local-admin-token").authorize(request)
        )

    def test_rejects_missing_or_wrong_credentials(self):
        authorizer = BearerTokenAuthorizer("a-long-local-admin-token")

        for header in (None, "Basic abc", "Bearer wrong"):
            with self.subTest(header=header):
                headers = {} if header is None else {"authorization": header}
                request = AdminRequest("GET", "/admin/health", headers)
                self.assertFalse(authorizer.authorize(request))

    def test_rejects_a_weak_configured_token(self):
        for token in (" ", "too-short"):
            with self.subTest(token=token):
                with self.assertRaises(ValueError):
                    BearerTokenAuthorizer(token)


if __name__ == "__main__":
    unittest.main()
