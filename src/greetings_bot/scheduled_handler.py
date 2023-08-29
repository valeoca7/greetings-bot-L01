import os
from typing import Any, Dict, List, Mapping, Optional

from greetings_bot.clock import FixedClock
from greetings_bot.deliveries import DeliveryLedger
from greetings_bot.dynamo_deliveries import DynamoDeliveryLedger
from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.scheduled_event import event_time
from greetings_bot.reminder_dispatcher import ReminderDispatcher
from greetings_bot.reminder_store import (
    InMemoryReminderRepository,
    ReminderRepository,
)
from greetings_bot.scheduler import GreetingDispatcher
from greetings_bot.telegram import reply_batch
from greetings_bot.users import UserRepository
from greetings_bot.users import InMemoryUserRepository


ScheduledResponse = List[Dict[str, object]]


class ScheduledGreetingHandler:
    def __init__(
        self,
        users: UserRepository,
        deliveries: Optional[DeliveryLedger] = None,
        max_batch: int = 100,
        reminders: Optional[ReminderRepository] = None,
        include_reminders: bool = True,
    ) -> None:
        self.users = users
        self.deliveries = deliveries
        self.max_batch = max_batch
        self.reminders = (
            reminders if reminders is not None else InMemoryReminderRepository()
        )
        self.include_reminders = include_reminders

    def handle(self, event: Mapping[str, Any]) -> ScheduledResponse:
        clock = FixedClock(event_time(event))
        dispatcher = GreetingDispatcher(
            self.users,
            clock,
            self.deliveries,
            self.max_batch,
        )
        replies = dispatcher.dispatch()
        if self.include_reminders:
            replies.extend(
                ReminderDispatcher(
                    self.reminders, clock, self.max_batch
                ).dispatch()
            )
        return reply_batch(replies)


def build_default_handler(
    environ: Mapping[str, str] = os.environ,
    dynamodb_resource: DynamoResource = None,
) -> ScheduledGreetingHandler:
    max_batch = int(environ.get("DISPATCH_BATCH_SIZE", "100"))
    include_reminders = environ.get("TARGETED_REMINDERS") != "true"
    table_name = environ.get("USER_TABLE_NAME")
    if not table_name:
        return ScheduledGreetingHandler(
            InMemoryUserRepository(),
            max_batch=max_batch,
            include_reminders=include_reminders,
        )
    users = repository_for_table(table_name, dynamodb_resource)
    deliveries = DynamoDeliveryLedger(users.table)
    reminders = DynamoReminderRepository(users.table)
    return ScheduledGreetingHandler(
        users, deliveries, max_batch, reminders, include_reminders
    )


_handler = build_default_handler()


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> ScheduledResponse:
    return _handler.handle(event)
