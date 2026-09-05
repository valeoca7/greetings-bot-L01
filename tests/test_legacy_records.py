import unittest
from datetime import datetime, timezone

from greetings_bot.dynamo_configuration_audit import audit_record_from_item
from greetings_bot.dynamo_reminders import reminder_from_item
from greetings_bot.users import user_from_dict


class LegacyRecordCompatibilityTest(unittest.TestCase):
    def test_reads_a_profile_from_before_delivery_preferences(self):
        user = user_from_dict(
            {"telegram_id": 42, "chat_id": 84, "first_name": "Mira"}
        )

        self.assertEqual(user.timezone, "UTC")
        self.assertEqual(
            user.greeting_days,
            ("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
        )
        self.assertEqual(user.digest_mode, "off")
        self.assertEqual(user.greeting_template_category, "friendly")
        self.assertIsNone(user.weather_location)

    def test_reads_a_reminder_from_before_recurrence(self):
        reminder = reminder_from_item(
            {
                "reminder_id": "abc12345",
                "owner_id": 42,
                "chat_id": 84,
                "text": "call home",
                "due_at": "2023-04-12T18:00:00+00:00",
                "created_at": "2023-04-01T18:00:00+00:00",
            }
        )

        self.assertEqual(reminder.status, "pending")
        self.assertIsNone(reminder.recurrence)
        self.assertEqual(reminder.timezone, "UTC")

    def test_reads_an_audit_record_without_changed_keys(self):
        record = audit_record_from_item(
            {
                "audit_id": "audit-1",
                "occurred_at": datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat(),
                "category": "configuration",
                "action": "configuration_loaded",
                "source": "deployment",
                "request_id": "startup",
            }
        )

        self.assertEqual(record.changed_keys, ())


if __name__ == "__main__":
    unittest.main()
