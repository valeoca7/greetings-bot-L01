import unittest
from datetime import datetime, timezone

from greetings_bot.user_deletion import request_deletion
from greetings_bot.user_deletion_store import (
    InMemoryDeletionRequestRepository,
)


class DeletionRequestRepositoryTest(unittest.TestCase):
    def test_saves_one_request_for_each_user(self):
        repository = InMemoryDeletionRequestRepository()
        current_time = datetime(2025, 8, 21, 3, 0, tzinfo=timezone.utc)
        first = request_deletion(
            42, "first-deletion-token", current_time
        )
        replacement = request_deletion(
            42, "replacement-token-1", current_time
        )

        repository.save(first)
        repository.save(replacement)

        self.assertEqual(repository.get(42), replacement)
        self.assertIsNone(repository.get(7))


if __name__ == "__main__":
    unittest.main()
