import unittest
from datetime import datetime, timezone

from greetings_bot.reminders import Reminder, create_reminder, mark_sent
from greetings_bot.users import User


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

    def test_creates_reminder_from_user_local_time(self):
        user = User(42, 84, "Mira", timezone="America/Vancouver")
        now = datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc)

        reminder = create_reminder(
            user, "2023-03-08", "09:30", "Call home", now
        )

        self.assertEqual(
            reminder.due_at,
            datetime(2023, 3, 8, 17, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(reminder.text, "Call home")

    def test_rejects_past_reminder(self):
        user = User(42, 84, "Mira")

        with self.assertRaisesRegex(ValueError, "future"):
            create_reminder(
                user,
                "2023-03-07",
                "09:30",
                "Old",
                datetime(2023, 3, 7, 10, 0, tzinfo=timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
