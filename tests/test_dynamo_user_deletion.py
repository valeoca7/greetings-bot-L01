import unittest
from datetime import datetime, timedelta, timezone

from greetings_bot.dynamo_user_deletion import (
    DynamoDeletionRequestRepository,
    deletion_request_from_item,
    deletion_request_item,
    deletion_request_key,
)
from greetings_bot.user_deletion import confirm_deletion, request_deletion


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, *, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}

    def get_item(self, *, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {} if item is None else {"Item": item}


class DeletionRequestMappingTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2025, 9, 11, 3, 0, tzinfo=timezone.utc)
        self.request = request_deletion(
            42, "delete-this-account-token", self.now
        )

    def test_uses_a_separate_ttl_backed_partition(self):
        item = deletion_request_item(self.request)

        self.assertEqual(
            deletion_request_key(42),
            {"pk": "DELETION#42", "sk": "REQUEST"},
        )
        self.assertEqual(
            item["expires_at"], int(self.request.expires_at.timestamp())
        )
        self.assertNotEqual(item["token_digest"], "delete-this-account-token")

    def test_round_trips_confirmation_state(self):
        confirmed = confirm_deletion(
            self.request,
            "delete-this-account-token",
            self.now + timedelta(minutes=1),
        )

        restored = deletion_request_from_item(
            deletion_request_item(confirmed)
        )

        self.assertEqual(restored, confirmed)


class DynamoDeletionRequestRepositoryTest(unittest.TestCase):
    def test_saves_and_loads_one_users_request(self):
        table = FakeTable()
        repository = DynamoDeletionRequestRepository(table)
        request = request_deletion(
            42,
            "delete-this-account-token",
            datetime(2025, 9, 11, 3, 0, tzinfo=timezone.utc),
        )

        repository.save(request)

        self.assertEqual(repository.get(42), request)
        self.assertIsNone(repository.get(7))


if __name__ == "__main__":
    unittest.main()
