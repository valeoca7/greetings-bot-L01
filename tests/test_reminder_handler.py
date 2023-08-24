import unittest
from datetime import datetime, timezone

from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.reminder_handler import (
    ScheduledReminderHandler,
    build_default_handler,
)
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import Reminder


class ScheduledReminderHandlerTest(unittest.TestCase):
    def test_delivers_named_pending_reminder(self):
        reminders = InMemoryReminderRepository()
        reminders.save(
            Reminder(
                "abcd1234", 42, 84, "Call home",
                datetime(2023, 8, 21, 18, 0, tzinfo=timezone.utc),
                datetime(2023, 8, 1, 18, 0, tzinfo=timezone.utc),
            )
        )

        reply = ScheduledReminderHandler(reminders).handle(
            {"owner_id": 42, "reminder_id": "abcd1234"}
        )

        self.assertEqual(reply, {"chat_id": 84, "text": "Reminder: Call home"})
        self.assertEqual(reminders.get(42, "abcd1234").status, "sent")

    def test_ignores_missing_or_inactive_reminder(self):
        handler = ScheduledReminderHandler(InMemoryReminderRepository())

        self.assertIsNone(handler.handle({"owner_id": 42, "reminder_id": "missing"}))
        self.assertIsNone(handler.handle({}))

    def test_builds_dynamo_handler_from_table_name(self):
        class Resource:
            def Table(self, name):
                self.name = name
                return object()

        resource = Resource()

        handler = build_default_handler({"USER_TABLE_NAME": "data"}, resource)

        self.assertEqual(resource.name, "data")
        self.assertIsInstance(handler.reminders, DynamoReminderRepository)


if __name__ == "__main__":
    unittest.main()
