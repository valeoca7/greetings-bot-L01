import unittest
from datetime import datetime, timezone

from greetings_bot.dynamo_reminders import (
    reminder_from_item,
    reminder_item,
    reminder_key,
)
from greetings_bot.reminders import Reminder


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


if __name__ == "__main__":
    unittest.main()
