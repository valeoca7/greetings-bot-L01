import os
from typing import Any, Dict, List, Mapping, Optional

from greetings_bot.clock import FixedClock
from greetings_bot.deliveries import DeliveryLedger
from greetings_bot.dynamo_deliveries import DynamoDeliveryLedger
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.scheduled_event import event_time
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
    ) -> None:
        self.users = users
        self.deliveries = deliveries
        self.max_batch = max_batch

    def handle(self, event: Mapping[str, Any]) -> ScheduledResponse:
        dispatcher = GreetingDispatcher(
            self.users,
            FixedClock(event_time(event)),
            self.deliveries,
            self.max_batch,
        )
        return reply_batch(dispatcher.dispatch())


def build_default_handler(
    environ: Mapping[str, str] = os.environ,
    dynamodb_resource: DynamoResource = None,
) -> ScheduledGreetingHandler:
    table_name = environ.get("USER_TABLE_NAME")
    if not table_name:
        return ScheduledGreetingHandler(InMemoryUserRepository())
    users = repository_for_table(table_name, dynamodb_resource)
    deliveries = DynamoDeliveryLedger(users.table)
    return ScheduledGreetingHandler(users, deliveries)


_handler = build_default_handler()


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> ScheduledResponse:
    return _handler.handle(event)
