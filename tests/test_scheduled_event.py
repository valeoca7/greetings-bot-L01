import unittest
from datetime import datetime, timezone

from greetings_bot.scheduled_event import ScheduledEventError, event_time


class ScheduledEventTest(unittest.TestCase):
    def test_parses_eventbridge_time(self):
        parsed = event_time({"time": "2023-01-10T18:30:00Z"})

        self.assertEqual(parsed, datetime(2023, 1, 10, 18, 30, tzinfo=timezone.utc))

    def test_requires_time(self):
        with self.assertRaisesRegex(ScheduledEventError, "required"):
            event_time({})

    def test_rejects_time_without_offset(self):
        with self.assertRaisesRegex(ScheduledEventError, "offset"):
            event_time({"time": "2023-01-10T18:30:00"})


if __name__ == "__main__":
    unittest.main()
