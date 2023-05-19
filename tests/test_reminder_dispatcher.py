import unittest
from datetime import datetime, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.reminder_dispatcher import ReminderDispatcher
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import Reminder
from greetings_bot.telegram import Reply


class ReminderDispatcherTest(unittest.TestCase):
    def test_dispatches_and_marks_due_reminder(self):
        reminders = InMemoryReminderRepository()
        reminder = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )
        reminders.save(reminder)
        dispatcher = ReminderDispatcher(
            reminders,
            FixedClock(datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc)),
        )

        replies = dispatcher.dispatch()

        self.assertEqual(replies, [Reply(84, "Reminder: Call home")])
        self.assertEqual(reminders.get(42, "abcd1234").status, "sent")

    def test_does_not_repeat_sent_reminder(self):
        reminders = InMemoryReminderRepository()
        reminder = Reminder(
            "abcd1234", 42, 84, "Call home",
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 7, 18, 0, tzinfo=timezone.utc),
        )
        reminders.save(reminder)
        dispatcher = ReminderDispatcher(
            reminders,
            FixedClock(datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc)),
        )

        dispatcher.dispatch()

        self.assertEqual(dispatcher.dispatch(), [])

    def test_advances_recurring_reminder(self):
        reminders = InMemoryReminderRepository()
        reminder = Reminder(
            "abcd1234", 42, 84, "Drink water",
            datetime(2023, 5, 2, 16, 0, tzinfo=timezone.utc),
            datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            recurrence="daily",
            timezone="America/Vancouver",
        )
        reminders.save(reminder)
        dispatcher = ReminderDispatcher(
            reminders,
            FixedClock(datetime(2023, 5, 2, 16, 0, tzinfo=timezone.utc)),
        )

        dispatcher.dispatch()

        advanced = reminders.get(42, "abcd1234")
        self.assertEqual(advanced.status, "pending")
        self.assertEqual(
            advanced.due_at,
            datetime(2023, 5, 3, 16, 0, tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
