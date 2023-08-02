import json
from dataclasses import dataclass
from typing import Dict

from greetings_bot.reminders import Reminder


@dataclass(frozen=True)
class ScheduleTarget:
    arn: str
    role_arn: str


def reminder_schedule_name(reminder: Reminder) -> str:
    return "reminder-{}-{}".format(reminder.owner_id, reminder.id)


def create_schedule_request(
    reminder: Reminder,
    target: ScheduleTarget,
    group_name: str = "greetings-bot",
) -> Dict[str, object]:
    expression = reminder.due_at.strftime("at(%Y-%m-%dT%H:%M:%S)")
    payload = json.dumps(
        {"owner_id": reminder.owner_id, "reminder_id": reminder.id}
    )
    return {
        "Name": reminder_schedule_name(reminder),
        "GroupName": group_name,
        "ScheduleExpression": expression,
        "ScheduleExpressionTimezone": "UTC",
        "FlexibleTimeWindow": {"Mode": "OFF"},
        "ActionAfterCompletion": "DELETE",
        "Target": {
            "Arn": target.arn,
            "RoleArn": target.role_arn,
            "Input": payload,
        },
    }
