import unittest
from datetime import datetime, timedelta, timezone

from greetings_bot.reminders import (
    Reminder,
    cancel_reminder,
    create_daily_reminder,
    create_weekly_reminder,
    complete_reminder,
    edit_reminder_text,
    create_reminder,
    format_reminder_list,
    format_reminder,
    local_to_utc,
    parse_clock_time,
    parse_snooze_duration,
    pause_reminder,
    resume_reminder,
    snooze_reminder,
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

    def test_pauses_and_resumes_pending_reminder(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 6, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 5, 1, 18, 0, tzinfo=timezone.utc),
        )

        paused = pause_reminder(reminder)
        resumed = resume_reminder(paused)

        self.assertEqual(paused.status, "paused")
        self.assertEqual(resumed.status, "pending")

    def test_edits_active_reminder_text(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Old text",
            datetime(2023, 6, 5, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 5, 1, 18, 0, tzinfo=timezone.utc),
        )

        edited = edit_reminder_text(reminder, "  New text  ")

        self.assertEqual(edited.text, "New text")

    def test_cancels_active_reminder(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Old text",
            datetime(2023, 6, 5, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 5, 1, 18, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(cancel_reminder(reminder).status, "cancelled")

    def test_parses_snooze_units(self):
        self.assertEqual(parse_snooze_duration("15m"), timedelta(minutes=15))
        self.assertEqual(parse_snooze_duration("2h"), timedelta(hours=2))
        self.assertEqual(parse_snooze_duration("1d"), timedelta(days=1))

    def test_limits_snooze_to_one_week(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            parse_snooze_duration("8d")

    def test_snoozes_from_current_time(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 6, 12, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 5, 1, 18, 0, tzinfo=timezone.utc),
            status="paused",
        )
        now = datetime(2023, 6, 12, 19, 0, tzinfo=timezone.utc)

        snoozed = snooze_reminder(reminder, timedelta(minutes=30), now)

        self.assertEqual(
            snoozed.due_at,
            datetime(2023, 6, 12, 19, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(snoozed.status, "pending")

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

    def test_formats_reminder_details(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Drink water",
            datetime(2023, 6, 14, 16, 0, tzinfo=timezone.utc),
            datetime(2023, 5, 1, 18, 0, tzinfo=timezone.utc),
            recurrence="daily",
            timezone="America/Vancouver",
        )

        text = format_reminder(reminder, "America/Vancouver")

        self.assertEqual(
            text,
            "Drink water\nDue: 2023-06-14 09:00\nStatus: pending\nRepeat: daily",
        )

    def test_formats_reminder_details_in_ukrainian(self):
        reminder = Reminder(
            "abcd1234", 42, 84, "Випити води",
            datetime(2023, 6, 14, 16, 0, tzinfo=timezone.utc),
            datetime(2023, 5, 1, 18, 0, tzinfo=timezone.utc),
            recurrence="daily",
            timezone="America/Vancouver",
        )

        text = format_reminder(
            reminder, "America/Vancouver", locale="uk"
        )

        self.assertEqual(
            text,
            "Випити води\nТермін: 2023-06-14 09:00\n"
            "Статус: активне\nПовтор: щодня",
        )

    def test_rejects_time_skipped_by_spring_clock_change(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            local_to_utc(
                datetime(2023, 3, 12, 2, 30),
                "America/Vancouver",
            )

    def test_recurring_time_requires_hour_and_minute(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            parse_clock_time("09:30:15")

    def test_creates_next_daily_occurrence(self):
        user = User(42, 84, "Mira", timezone="America/Vancouver")
        now = datetime(2023, 4, 24, 18, 0, tzinfo=timezone.utc)

        reminder = create_daily_reminder(user, "09:00", "Drink water", now)

        self.assertEqual(reminder.recurrence, "daily")
        self.assertEqual(
            reminder.due_at,
            datetime(2023, 4, 25, 16, 0, tzinfo=timezone.utc),
        )

    def test_daily_can_start_later_today(self):
        user = User(42, 84, "Mira", timezone="America/Vancouver")
        now = datetime(2023, 4, 24, 16, 0, tzinfo=timezone.utc)

        reminder = create_daily_reminder(user, "10:00", "Break", now)

        self.assertEqual(
            reminder.due_at,
            datetime(2023, 4, 24, 17, 0, tzinfo=timezone.utc),
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

    def test_weekly_can_start_later_on_matching_weekday(self):
        user = User(42, 84, "Mira", timezone="America/Vancouver")
        now = datetime(2023, 5, 22, 16, 0, tzinfo=timezone.utc)

        reminder = create_weekly_reminder(
            user, "monday", "10:00", "Plan", now
        )

        self.assertEqual(
            reminder.due_at,
            datetime(2023, 5, 22, 17, 0, tzinfo=timezone.utc),
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
