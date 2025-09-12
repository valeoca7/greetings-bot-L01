import unittest

from datetime import datetime, timezone

from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.notes import Note
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import Reminder
from greetings_bot.user_data_cleanup import (
    DynamoUserDataCleaner,
    RepositoryUserDataCleaner,
)
from greetings_bot.users import InMemoryUserRepository, User


class FakeTable:
    def __init__(self, items):
        self.items = {
            (item["pk"], item["sk"]): dict(item) for item in items
        }

    def query(self, **kwargs):
        partition = kwargs["ExpressionAttributeValues"][":pk"]
        items = [
            item for (pk, _), item in sorted(self.items.items())
            if pk == partition
        ]
        return {"Items": items[: kwargs["Limit"]]}

    def delete_item(self, *, Key):
        self.items.pop((Key["pk"], Key["sk"]), None)
        return {}


def item(owner_id, sort_key, entity):
    return {
        "pk": "USER#{}".format(owner_id),
        "sk": sort_key,
        "entity": entity,
    }


class UserDataCleanupTest(unittest.TestCase):
    def test_deletes_only_one_users_bounded_batch(self):
        table = FakeTable(
            [
                item(42, "NOTE#a", "note"),
                item(42, "NOTE#b", "note"),
                item(42, "PROFILE", "user"),
                item(7, "NOTE#other", "note"),
            ]
        )
        cleaner = DynamoUserDataCleaner(table)

        batch = cleaner.erase_batch(42, limit=1)

        self.assertEqual(batch.deleted, 1)
        self.assertFalse(batch.complete)
        self.assertIn(("USER#42", "PROFILE"), table.items)
        self.assertIn(("USER#7", "NOTE#other"), table.items)

    def test_deletes_profile_only_after_other_records(self):
        table = FakeTable(
            [
                item(42, "DELIVERY#2025-08-01", "delivery"),
                item(42, "INFO_QUOTA#2025-W35", "information_quota"),
                item(42, "PROFILE", "user"),
                item(42, "REMINDER#a", "reminder"),
            ]
        )
        cleaner = DynamoUserDataCleaner(table)

        first = cleaner.erase_batch(42, limit=2)
        second = cleaner.erase_batch(42, limit=2)
        final = cleaner.erase_batch(42, limit=2)

        self.assertFalse(first.complete)
        self.assertFalse(second.complete)
        self.assertTrue(final.complete)
        self.assertEqual(final.deleted, 1)
        self.assertNotIn(("USER#42", "PROFILE"), table.items)

    def test_empty_partition_is_already_complete(self):
        batch = DynamoUserDataCleaner(FakeTable([])).erase_batch(42)

        self.assertEqual(batch.deleted, 0)
        self.assertTrue(batch.complete)

    def test_rejects_an_unbounded_batch(self):
        cleaner = DynamoUserDataCleaner(FakeTable([]))

        for limit in (0, 101):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    cleaner.erase_batch(42, limit)


class RepositoryUserDataCleanupTest(unittest.TestCase):
    def test_erases_records_before_the_profile(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        reminders = InMemoryReminderRepository()
        now = datetime(2025, 9, 11, 3, 0, tzinfo=timezone.utc)
        users.save(User(42, 4200, "Mira"))
        notes.save(Note("note", 42, "Private", now))
        reminders.save(
            Reminder("reminder", 42, 4200, "Private", now, now)
        )
        cleaner = RepositoryUserDataCleaner(users, notes, reminders)

        first = cleaner.erase_batch(42, limit=1)
        second = cleaner.erase_batch(42, limit=1)
        final = cleaner.erase_batch(42, limit=1)

        self.assertFalse(first.complete)
        self.assertFalse(second.complete)
        self.assertTrue(final.complete)
        self.assertIsNone(users.get(42))


if __name__ == "__main__":
    unittest.main()
