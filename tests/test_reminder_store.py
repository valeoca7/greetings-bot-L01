import unittest
from datetime import datetime, timezone

from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import Reminder


def reminder(owner_id=42, reminder_id="abcd1234", status="pending"):
    return Reminder(
        reminder_id, owner_id, owner_id, "Call home",
        datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
        datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        status,
    )


class InMemoryReminderRepositoryTest(unittest.TestCase):
    def test_saves_owned_reminder(self):
        reminders = InMemoryReminderRepository()
        value = reminder()

        reminders.save(value)

        self.assertEqual(reminders.get(42, "abcd1234"), value)
        self.assertIsNone(reminders.get(7, "abcd1234"))


if __name__ == "__main__":
    unittest.main()
