import unittest
from datetime import datetime, timezone

from greetings_bot.reminders import (
    Reminder,
    create_daily_reminder,
    create_weekly_reminder,
    complete_reminder,
    create_reminder,
    format_reminder_list,
    local_to_utc,
    mark_sent,
)
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

    def test_one_time_reminder_has_no_recurrence(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 6, 20, 0, tzinfo=timezone.utc),
        )

        self.assertIsNone(reminder.recurrence)
        self.assertEqual(reminder.timezone, "UTC")

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
        self.assertEqual(reminder.timezone, "America/Vancouver")

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

    def test_formats_due_time_in_user_timezone(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 4, 1, 16, 30, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )

        text = format_reminder_list([reminder], "America/Vancouver")

        self.assertEqual(text, "abcd1234: 2023-04-01 09:30 Call home (pending)")

    def test_labels_recurring_reminder_in_list(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Drink water",
            datetime(2023, 5, 9, 16, 0, tzinfo=timezone.utc),
            datetime(2023, 5, 1, 18, 0, tzinfo=timezone.utc),
            recurrence="daily",
            timezone="America/Vancouver",
        )

        text = format_reminder_list([reminder], "America/Vancouver")

        self.assertIn("(pending, daily)", text)

    def test_rejects_time_skipped_by_spring_clock_change(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            local_to_utc(
                datetime(2023, 3, 12, 2, 30),
                "America/Vancouver",
            )

    def test_creates_next_daily_occurrence(self):
        user = User(42, 84, "Mira", timezone="America/Vancouver")
        now = datetime(2023, 4, 24, 18, 0, tzinfo=timezone.utc)

        reminder = create_daily_reminder(user, "09:00", "Drink water", now)

        self.assertEqual(reminder.recurrence, "daily")
        self.assertEqual(
            reminder.due_at,
            datetime(2023, 4, 25, 16, 0, tzinfo=timezone.utc),
        )

    def test_creates_next_weekly_occurrence(self):
        user = User(42, 84, "Mira", timezone="America/Vancouver")
        now = datetime(2023, 4, 25, 18, 0, tzinfo=timezone.utc)

        reminder = create_weekly_reminder(
            user, "monday", "09:00", "Plan week", now
        )

        self.assertEqual(reminder.recurrence, "weekly")
        self.assertEqual(
            reminder.due_at,
            datetime(2023, 5, 1, 16, 0, tzinfo=timezone.utc),
        )

    def test_daily_occurrence_keeps_wall_time_across_fall_change(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Daily",
            datetime(2023, 11, 4, 16, 0, tzinfo=timezone.utc),
            datetime(2023, 10, 1, 18, 0, tzinfo=timezone.utc),
            recurrence="daily",
            timezone="America/Vancouver",
        )

        advanced = complete_reminder(reminder)

        self.assertEqual(
            advanced.due_at,
            datetime(2023, 11, 5, 17, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(advanced.status, "pending")

    def test_daily_occurrence_skips_nonexistent_wall_time(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Daily",
            datetime(2023, 3, 11, 10, 30, tzinfo=timezone.utc),
            datetime(2023, 3, 1, 18, 0, tzinfo=timezone.utc),
            recurrence="daily",
            timezone="America/Vancouver",
        )

        advanced = complete_reminder(reminder)

        self.assertEqual(
            advanced.due_at,
            datetime(2023, 3, 13, 9, 30, tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
