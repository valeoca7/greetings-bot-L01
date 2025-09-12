import unittest
from datetime import datetime, timedelta, timezone

from greetings_bot.user_deletion import (
    complete_deletion,
    confirm_deletion,
    request_deletion,
)


class UserDeletionTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2025, 8, 20, 3, 0, tzinfo=timezone.utc)
        self.token = "delete-account-token-123"

    def test_requests_deletion_without_storing_the_token(self):
        request = request_deletion(42, self.token, self.now)

        self.assertEqual(request.status, "requested")
        self.assertEqual(request.telegram_id, 42)
        self.assertEqual(request.expires_at, self.now + timedelta(minutes=30))
        self.assertNotEqual(request.token_digest, self.token)
        self.assertNotIn(self.token, repr(request))

    def test_confirms_a_matching_unexpired_token(self):
        request = request_deletion(42, self.token, self.now)

        confirmed = confirm_deletion(
            request, self.token, self.now + timedelta(minutes=5)
        )

        self.assertEqual(confirmed.status, "confirmed")
        self.assertEqual(
            confirmed.confirmed_at, self.now + timedelta(minutes=5)
        )

    def test_rejects_wrong_expired_or_reused_confirmation(self):
        request = request_deletion(42, self.token, self.now)
        confirmed = confirm_deletion(request, self.token, self.now)

        cases = (
            (request, "wrong-token-value", self.now),
            (request, self.token, request.expires_at),
            (confirmed, self.token, self.now),
        )
        for candidate, token, current_time in cases:
            with self.subTest(token=token, current_time=current_time):
                with self.assertRaises(ValueError):
                    confirm_deletion(candidate, token, current_time)

    def test_completes_only_a_confirmed_request(self):
        request = request_deletion(42, self.token, self.now)

        with self.assertRaises(ValueError):
            complete_deletion(request, self.now)

        confirmed = confirm_deletion(request, self.token, self.now)
        completed = complete_deletion(
            confirmed, self.now + timedelta(seconds=1)
        )

        self.assertEqual(completed.status, "completed")
        self.assertEqual(
            completed.completed_at, self.now + timedelta(seconds=1)
        )

    def test_requires_aware_times_and_bounded_tokens(self):
        with self.assertRaises(ValueError):
            request_deletion(42, self.token, datetime(2025, 8, 20, 3, 0))
        with self.assertRaises(ValueError):
            request_deletion(42, "short", self.now)
        with self.assertRaises(ValueError):
            request_deletion(
                42, self.token, self.now, timedelta(hours=2)
            )


if __name__ == "__main__":
    unittest.main()
