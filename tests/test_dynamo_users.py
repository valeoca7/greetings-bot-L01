import unittest

from greetings_bot.dynamo_users import (
    DynamoUserRepository,
    repository_for_table,
    user_from_item,
    user_item,
    user_key,
)
from greetings_bot.users import User


class FakeTable:
    def __init__(self):
        self.items = {}
        self.pages = None
        self.scan_requests = []

    def put_item(self, *, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}

    def get_item(self, *, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {} if item is None else {"Item": item}

    def scan(self, **kwargs):
        self.scan_requests.append(kwargs)
        if self.pages is not None:
            page = 0 if "ExclusiveStartKey" not in kwargs else 1
            result = {"Items": self.pages[page]}
            if page == 0:
                result["LastEvaluatedKey"] = {"pk": "next", "sk": "next"}
            return result
        return {"Items": list(self.items.values())}

    def delete_item(self, **kwargs):
        key = kwargs["Key"]
        item = self.items.pop((key["pk"], key["sk"]), None)
        return {} if item is None else {"Attributes": item}


class FakeResource:
    def __init__(self, table):
        self.table = table
        self.requested_name = None

    def Table(self, name):
        self.requested_name = name
        return self.table


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

    def test_ignores_other_table_entities(self):
        table = FakeTable()
        table.items[("CONFIG#bot", "CURRENT")] = {
            "pk": "CONFIG#bot",
            "sk": "CURRENT",
            "entity": "config",
        }
        users = DynamoUserRepository(table)

        self.assertEqual(users.all(), [])

    def test_reads_all_scan_pages(self):
        table = FakeTable()
        table.pages = [
            [user_item(User(42, 84, "Mira"))],
            [user_item(User(7, 14, "Leo"))],
        ]

        users = DynamoUserRepository(table).all()

        self.assertEqual([user.telegram_id for user in users], [7, 42])

    def test_iterates_bounded_scan_pages_lazily(self):
        table = FakeTable()
        table.pages = [
            [user_item(User(1, 1, "One"))],
            [user_item(User(2, 2, "Two"))],
        ]
        users = DynamoUserRepository(table).iter_all(page_size=25)

        first = next(iter(users))

        self.assertEqual(first.telegram_id, 1)
        self.assertEqual(len(table.scan_requests), 1)
        self.assertEqual(table.scan_requests[0]["Limit"], 25)

    def test_rejects_an_unbounded_scan_page(self):
        with self.assertRaises(ValueError):
            list(DynamoUserRepository(FakeTable()).iter_all(page_size=501))

    def test_deletes_a_user_profile(self):
        users = DynamoUserRepository(FakeTable())
        users.save(User(42, 84, "Mira"))

        self.assertTrue(users.delete(42))
        self.assertFalse(users.delete(42))
        self.assertIsNone(users.get(42))

    def test_builds_repository_from_named_table(self):
        resource = FakeResource(FakeTable())

        users = repository_for_table("greetings-users", resource)
        users.save(User(42, 84, "Mira"))

        self.assertEqual(resource.requested_name, "greetings-users")


if __name__ == "__main__":
    unittest.main()
