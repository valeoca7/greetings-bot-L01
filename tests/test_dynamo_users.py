import unittest

from greetings_bot.dynamo_users import (
    DynamoUserRepository,
    user_from_item,
    user_item,
    user_key,
)
from greetings_bot.users import User


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, *, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}

    def get_item(self, *, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {} if item is None else {"Item": item}

    def scan(self, **kwargs):
        return {"Items": list(self.items.values())}


class UserKeyTest(unittest.TestCase):
    def test_builds_user_profile_key(self):
        self.assertEqual(
            user_key(42),
            {"pk": "USER#42", "sk": "PROFILE"},
        )

    def test_maps_user_to_an_item(self):
        item = user_item(User(42, 84, "Mira"))

        self.assertEqual(item["pk"], "USER#42")
        self.assertEqual(item["sk"], "PROFILE")
        self.assertEqual(item["entity"], "user")
        self.assertEqual(item["first_name"], "Mira")

    def test_restores_user_from_an_item(self):
        original = User(42, 84, "Mira", timezone="America/Vancouver")

        restored = user_from_item(user_item(original))

        self.assertEqual(restored, original)


class DynamoUserRepositoryTest(unittest.TestCase):
    def test_saves_user_item(self):
        table = FakeTable()
        users = DynamoUserRepository(table)

        users.save(User(42, 84, "Mira"))

        self.assertEqual(table.items[("USER#42", "PROFILE")]["first_name"], "Mira")

    def test_gets_user_by_telegram_id(self):
        users = DynamoUserRepository(FakeTable())
        users.save(User(42, 84, "Mira"))

        self.assertEqual(users.get(42), User(42, 84, "Mira"))

    def test_returns_none_for_missing_user(self):
        users = DynamoUserRepository(FakeTable())

        self.assertIsNone(users.get(404))

    def test_lists_stored_users(self):
        users = DynamoUserRepository(FakeTable())
        users.save(User(42, 84, "Mira"))
        users.save(User(7, 14, "Leo"))

        self.assertEqual([user.telegram_id for user in users.all()], [7, 42])

    def test_counts_stored_users(self):
        users = DynamoUserRepository(FakeTable())
        users.save(User(42, 84, "Mira"))

        self.assertEqual(users.count(), 1)


if __name__ == "__main__":
    unittest.main()
