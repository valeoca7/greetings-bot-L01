import os
from typing import Dict, Mapping, Optional, Union

from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.reminder_store import ReminderRepository
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import complete_reminder
from greetings_bot.telegram import Reply, reply_payload


class ScheduledReminderHandler:
    def __init__(self, reminders: ReminderRepository) -> None:
        self.reminders = reminders

    def handle(
        self, event: Mapping[str, object]
    ) -> Optional[Dict[str, Union[int, str]]]:
        try:
            owner_id = int(event["owner_id"])
            reminder_id = str(event["reminder_id"])
        except (KeyError, TypeError, ValueError):
            return None
        reminder = self.reminders.get(owner_id, reminder_id)
        if reminder is None or reminder.status != "pending":
            return None
        reply = Reply(reminder.chat_id, "Reminder: {}".format(reminder.text))
        self.reminders.save(complete_reminder(reminder))
        return reply_payload(reply)


def build_default_handler(
    environ: Mapping[str, str] = os.environ,
    dynamodb_resource: DynamoResource = None,
) -> ScheduledReminderHandler:
    table_name = environ.get("USER_TABLE_NAME")
    if not table_name:
        return ScheduledReminderHandler(InMemoryReminderRepository())
    users = repository_for_table(table_name, dynamodb_resource)
    return ScheduledReminderHandler(DynamoReminderRepository(users.table))


_handler = build_default_handler()


def handle_event(event: Mapping[str, object], context: object = None):
    return _handler.handle(event)
