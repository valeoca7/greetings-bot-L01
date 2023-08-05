import json
import unittest
from datetime import datetime, timezone

from greetings_bot.event_scheduler import (
    EventBridgeReminderScheduler,
    ScheduleTarget,
    create_schedule_request,
    reminder_schedule_name,
)
from greetings_bot.reminders import Reminder


def reminder():
    return Reminder(
        "abcd1234", 42, 84, "Call home",
        datetime(2023, 8, 2, 18, 0, tzinfo=timezone.utc),
        datetime(2023, 8, 1, 18, 0, tzinfo=timezone.utc),
    )


class FakeSchedulerClient:
    def __init__(self):
        self.created = None
        self.deleted = None
        self.updated = None

    def create_schedule(self, **kwargs):
        self.created = kwargs
        return {}

    def delete_schedule(self, **kwargs):
        self.deleted = kwargs
        return {}

    def update_schedule(self, **kwargs):
        self.updated = kwargs
        return {}


class ScheduleRequestTest(unittest.TestCase):
    def test_builds_stable_schedule_name(self):
        self.assertEqual(reminder_schedule_name(reminder()), "reminder-42-abcd1234")

    def test_builds_one_time_utc_request(self):
        request = create_schedule_request(
            reminder(), ScheduleTarget("target-arn", "role-arn")
        )

        self.assertEqual(request["ScheduleExpression"], "at(2023-08-02T18:00:00)")
        self.assertEqual(request["ScheduleExpressionTimezone"], "UTC")
        self.assertEqual(request["FlexibleTimeWindow"], {"Mode": "OFF"})
        self.assertEqual(request["ActionAfterCompletion"], "DELETE")
        self.assertEqual(
            json.loads(request["Target"]["Input"]),
            {"owner_id": 42, "reminder_id": "abcd1234"},
        )


class EventBridgeReminderSchedulerTest(unittest.TestCase):
    def test_creates_schedule_through_client(self):
        client = FakeSchedulerClient()
        scheduler = EventBridgeReminderScheduler(
            client, ScheduleTarget("target-arn", "role-arn")
        )

        scheduler.create(reminder())

        self.assertEqual(client.created["Name"], "reminder-42-abcd1234")

    def test_deletes_schedule_by_name_and_group(self):
        client = FakeSchedulerClient()
        scheduler = EventBridgeReminderScheduler(
            client, ScheduleTarget("target-arn", "role-arn")
        )

        scheduler.delete(reminder())

        self.assertEqual(
            client.deleted,
            {"Name": "reminder-42-abcd1234", "GroupName": "greetings-bot"},
        )

    def test_updates_schedule_time(self):
        client = FakeSchedulerClient()
        scheduler = EventBridgeReminderScheduler(
            client, ScheduleTarget("target-arn", "role-arn")
        )

        scheduler.update(reminder())

        self.assertEqual(
            client.updated["ScheduleExpression"],
            "at(2023-08-02T18:00:00)",
        )


if __name__ == "__main__":
    unittest.main()
