import unittest
from datetime import datetime, timezone

from greetings_bot.dynamo_reminders import (
    DynamoReminderRepository,
    reminder_from_item,
    reminder_item,
    reminder_key,
)
from greetings_bot.reminders import Reminder


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, *, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}

    def get_item(self, *, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {} if item is None else {"Item": item}

    def query(self, **kwargs):
        if kwargs.get("IndexName") == "DueIndex":
            due = kwargs["ExpressionAttributeValues"][":due"]
            items = [
                item for item in self.items.values()
                if item.get("gsi1pk") == "REMINDER#PENDING"
                and item["gsi1sk"] <= due
            ]
            return {"Items": sorted(items, key=lambda item: item["gsi1sk"])[:kwargs["Limit"]]}
        owner = kwargs["ExpressionAttributeValues"][":pk"]
        return {
            "Items": [
                item for (pk, sk), item in self.items.items()
                if pk == owner and sk.startswith("REMINDER#")
            ]
        }


class ReminderMappingTest(unittest.TestCase):
    def setUp(self):
        self.reminder = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )

    def test_builds_owned_key(self):
        self.assertEqual(
            reminder_key(42, "abcd1234"),
            {"pk": "USER#42", "sk": "REMINDER#abcd1234"},
        )

    def test_pending_item_has_due_index_keys(self):
        item = reminder_item(self.reminder)

        self.assertEqual(item["gsi1pk"], "REMINDER#PENDING")
        self.assertTrue(item["gsi1sk"].startswith("2023-04-01T18:00:00+00:00"))
        self.assertEqual(reminder_from_item(item), self.reminder)

    def test_sent_item_leaves_due_index(self):
        sent = Reminder(**{**self.reminder.__dict__, "status": "sent"})

        self.assertNotIn("gsi1pk", reminder_item(sent))

    def test_paused_item_leaves_due_index(self):
        paused = Reminder(**{**self.reminder.__dict__, "status": "paused"})

        self.assertNotIn("gsi1pk", reminder_item(paused))

    def test_round_trips_recurrence_fields(self):
        recurring = Reminder(
            **{
                **self.reminder.__dict__,
                "recurrence": "weekly",
                "timezone": "America/Vancouver",
            }
        )

        self.assertEqual(reminder_from_item(reminder_item(recurring)), recurring)


class DynamoReminderRepositoryTest(unittest.TestCase):
    def test_saves_and_loads_owned_reminder(self):
        reminders = DynamoReminderRepository(FakeTable())
        value = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )

        reminders.save(value)

        self.assertEqual(reminders.get(42, "abcd1234"), value)
        self.assertIsNone(reminders.get(7, "abcd1234"))

    def test_lists_owner_reminders(self):
        reminders = DynamoReminderRepository(FakeTable())
        value = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )
        reminders.save(value)

        self.assertEqual(reminders.all_for(42), [value])
        self.assertEqual(reminders.all_for(7), [])

    def test_queries_due_index(self):
        reminders = DynamoReminderRepository(FakeTable())
        due = Reminder(
            "due", 42, 84, "Call home",
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )
        future = Reminder(
            "future", 7, 7, "Later",
            datetime(2023, 4, 2, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )
        reminders.save(due)
        reminders.save(future)

        selected = reminders.due_before(
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc), 10
        )

        self.assertEqual(selected, [due])


if __name__ == "__main__":
    unittest.main()
