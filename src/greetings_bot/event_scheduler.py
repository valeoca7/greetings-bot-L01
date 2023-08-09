import json
from dataclasses import dataclass
from typing import Dict, Mapping, Protocol

from greetings_bot.reminders import Reminder


@dataclass(frozen=True)
class ScheduleTarget:
    arn: str
    role_arn: str


class SchedulerClient(Protocol):
    def create_schedule(self, **kwargs: object) -> Mapping[str, object]:
        ...

    def delete_schedule(self, **kwargs: object) -> Mapping[str, object]:
        ...

    def update_schedule(self, **kwargs: object) -> Mapping[str, object]:
        ...


class ReminderSchedulePort(Protocol):
    def create(self, reminder: Reminder) -> None:
        ...

    def delete(self, reminder: Reminder) -> None:
        ...

    def update(self, reminder: Reminder) -> None:
        ...


class NoopReminderScheduler:
    def create(self, reminder: Reminder) -> None:
        pass

    def delete(self, reminder: Reminder) -> None:
        pass

    def update(self, reminder: Reminder) -> None:
        pass


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


class EventBridgeReminderScheduler:
    def __init__(
        self,
        client: SchedulerClient,
        target: ScheduleTarget,
        group_name: str = "greetings-bot",
    ) -> None:
        self.client = client
        self.target = target
        self.group_name = group_name

    def create(self, reminder: Reminder) -> None:
        self.client.create_schedule(
            **create_schedule_request(reminder, self.target, self.group_name)
        )

    def delete(self, reminder: Reminder) -> None:
        self.client.delete_schedule(
            Name=reminder_schedule_name(reminder),
            GroupName=self.group_name,
        )

    def update(self, reminder: Reminder) -> None:
        self.client.update_schedule(
            **create_schedule_request(reminder, self.target, self.group_name)
        )
