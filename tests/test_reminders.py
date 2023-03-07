import unittest
from datetime import datetime, timezone

from greetings_bot.reminders import Reminder, mark_sent


class ReminderTest(unittest.TestCase):
    def test_marks_reminder_sent(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 6, 20, 0, tzinfo=timezone.utc),
        )

        sent = mark_sent(reminder)

        self.assertEqual(sent.status, "sent")
        self.assertEqual(reminder.status, "pending")


if __name__ == "__main__":
    unittest.main()
