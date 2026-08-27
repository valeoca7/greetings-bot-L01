import json
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Protocol

from greetings_bot.aws_runtime import aws_client
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
        try:
            self.client.delete_schedule(
                Name=reminder_schedule_name(reminder),
                GroupName=self.group_name,
            )
        except Exception as error:
            if not _is_missing_schedule(error):
                raise

    def update(self, reminder: Reminder) -> None:
        self.client.update_schedule(
            **create_schedule_request(reminder, self.target, self.group_name)
        )


def scheduler_from_env(
    environ: Mapping[str, str],
    client: Optional[SchedulerClient] = None,
) -> ReminderSchedulePort:
    target_arn = environ.get("SCHEDULER_TARGET_ARN")
    role_arn = environ.get("SCHEDULER_ROLE_ARN")
    if not target_arn or not role_arn:
        return NoopReminderScheduler()
    if client is None:
        client = aws_client("scheduler")
    return EventBridgeReminderScheduler(
        client,
        ScheduleTarget(target_arn, role_arn),
        environ.get("SCHEDULER_GROUP", "greetings-bot"),
    )


def _is_missing_schedule(error: Exception) -> bool:
    response = getattr(error, "response", None)
    if not isinstance(response, Mapping):
        return False
    details = response.get("Error")
    return isinstance(details, Mapping) and details.get("Code") == (
        "ResourceNotFoundException"
    )
