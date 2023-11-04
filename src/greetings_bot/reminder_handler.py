import logging
import os
from typing import Dict, Mapping, Optional, Union

from greetings_bot.delivery_queue import (
    DeliveryMessage,
    DeliveryQueue,
    queue_from_env,
)
from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.observability import correlation_id, emit_metric, log_event
from greetings_bot.reminder_store import ReminderRepository
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import complete_reminder
from greetings_bot.telegram import Reply, reply_payload

LOGGER = logging.getLogger(__name__)


class ScheduledReminderHandler:
    def __init__(
        self,
        reminders: ReminderRepository,
        queue: Optional[DeliveryQueue] = None,
    ) -> None:
        self.reminders = reminders
        self.queue = queue

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
        if self.queue is not None:
            delivery_id = "reminder-{}-{}-{}".format(
                reminder.owner_id,
                reminder.id,
                int(reminder.due_at.timestamp()),
            )
            self.queue.enqueue(
                DeliveryMessage(
                    delivery_id, reply.chat_id, reply.text, "reminder"
                )
            )
        self.reminders.save(complete_reminder(reminder))
        return reply_payload(reply)


def build_default_handler(
    environ: Mapping[str, str] = os.environ,
    dynamodb_resource: DynamoResource = None,
) -> ScheduledReminderHandler:
    table_name = environ.get("USER_TABLE_NAME")
    if not table_name:
        return ScheduledReminderHandler(
            InMemoryReminderRepository(), queue_from_env(environ)
        )
    users = repository_for_table(table_name, dynamodb_resource)
    return ScheduledReminderHandler(
        DynamoReminderRepository(users.table), queue_from_env(environ)
    )


_handler = build_default_handler()


def handle_event(event: Mapping[str, object], context: object = None):
    request_id = correlation_id(event, context)
    reply = _handler.handle(event)
    prepared = int(reply is not None)
    log_event(
        LOGGER,
        "reminder_dispatch_complete",
        request_id=request_id,
        reminder_id=event.get("reminder_id"),
        prepared=prepared,
    )
    emit_metric(LOGGER, "reminder_dispatcher", "Prepared", prepared)
    return reply
