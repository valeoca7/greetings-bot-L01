import logging
import os
from typing import Any, Dict, List, Mapping, Optional

from greetings_bot.clock import FixedClock
from greetings_bot.delivery_queue import DeliveryMessage, DeliveryQueue, queue_from_env
from greetings_bot.deliveries import DeliveryLedger
from greetings_bot.dynamo_deliveries import DynamoDeliveryLedger
from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.observability import correlation_id, emit_metric, log_event
from greetings_bot.scheduled_event import event_time
from greetings_bot.reminder_dispatcher import ReminderDispatcher
from greetings_bot.reminder_store import (
    InMemoryReminderRepository,
    ReminderRepository,
)
from greetings_bot.retention import retention_from_env
from greetings_bot.scheduler import GreetingDispatcher
from greetings_bot.telegram import reply_batch
from greetings_bot.throughput import throughput_from_env
from greetings_bot.users import UserRepository
from greetings_bot.users import InMemoryUserRepository
from greetings_bot.usage import usage_meter_from_env
from greetings_bot.weather import WeatherProvider
from greetings_bot.weather_summary import add_weather_summaries
from greetings_bot.weather_runtime import reliable_weather_provider


ScheduledResponse = List[Dict[str, object]]
LOGGER = logging.getLogger(__name__)


class ScheduledGreetingHandler:
    def __init__(
        self,
        users: UserRepository,
        deliveries: Optional[DeliveryLedger] = None,
        max_batch: int = 100,
        reminders: Optional[ReminderRepository] = None,
        include_reminders: bool = True,
        queue: Optional[DeliveryQueue] = None,
        weather_provider: Optional[WeatherProvider] = None,
        queue_high_watermark: int = 1000,
    ) -> None:
        self.users = users
        self.deliveries = deliveries
        self.max_batch = max_batch
        self.reminders = (
            reminders if reminders is not None else InMemoryReminderRepository()
        )
        self.include_reminders = include_reminders
        self.queue = queue
        self.weather_provider = weather_provider
        self.queue_high_watermark = queue_high_watermark

    def handle(self, event: Mapping[str, Any]) -> ScheduledResponse:
        clock = FixedClock(event_time(event))
        if self.queue is not None:
            queue_depth = self.queue.depth()
            emit_metric(LOGGER, "dispatcher", "QueueDepth", queue_depth)
            if queue_depth >= self.queue_high_watermark:
                log_event(
                    LOGGER,
                    "scheduled_dispatch_paused",
                    queue_depth=queue_depth,
                    queue_high_watermark=self.queue_high_watermark,
                )
                emit_metric(LOGGER, "dispatcher", "Backpressure")
                return []
        dispatcher = GreetingDispatcher(
            self.users,
            clock,
            self.deliveries,
            self.max_batch,
        )
        users = self.users.iter_all()
        replies = dispatcher.dispatch(users)
        replies = add_weather_summaries(
            replies,
            dispatcher.dispatched_users,
            clock.now(),
            self.weather_provider,
        )
        if self.include_reminders:
            replies.extend(
                ReminderDispatcher(
                    self.reminders, clock, self.max_batch
                ).dispatch()
            )
        if self.queue is not None:
            event_stamp = clock.now().strftime("%Y%m%d%H%M")
            messages = []
            for reply in replies:
                kind = "reminder" if reply.text.startswith("Reminder:") else "greeting"
                messages.append(
                    DeliveryMessage(
                        "{}-{}-{}".format(kind, reply.chat_id, event_stamp),
                        reply.chat_id,
                        reply.text,
                        kind,
                    )
                )
            self.queue.enqueue_many(messages)
        return reply_batch(replies)


def build_default_handler(
    environ: Mapping[str, str] = os.environ,
    dynamodb_resource: DynamoResource = None,
) -> ScheduledGreetingHandler:
    throughput = throughput_from_env(environ)
    include_reminders = environ.get("TARGETED_REMINDERS") != "true"
    usage_meter = usage_meter_from_env(environ)
    queue = queue_from_env(environ, usage_meter=usage_meter)
    table_name = environ.get("USER_TABLE_NAME")
    if not table_name:
        weather_provider = reliable_weather_provider(
            environ, usage_meter=usage_meter
        )
        return ScheduledGreetingHandler(
            InMemoryUserRepository(),
            max_batch=throughput.dispatch_batch_size,
            include_reminders=include_reminders,
            queue=queue,
            weather_provider=weather_provider,
            queue_high_watermark=throughput.queue_high_watermark,
        )
    users = repository_for_table(table_name, dynamodb_resource)
    weather_provider = reliable_weather_provider(
        environ, users.table, usage_meter=usage_meter
    )
    retention = retention_from_env(environ)
    deliveries = DynamoDeliveryLedger(users.table, retention.delivery_days)
    reminders = DynamoReminderRepository(users.table)
    return ScheduledGreetingHandler(
        users,
        deliveries,
        throughput.dispatch_batch_size,
        reminders,
        include_reminders,
        queue,
        weather_provider,
        throughput.queue_high_watermark,
    )


_handler = build_default_handler()


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> ScheduledResponse:
    request_id = correlation_id(event, context)
    replies = _handler.handle(event)
    log_event(
        LOGGER, "scheduled_dispatch_complete", request_id=request_id, count=len(replies)
    )
    emit_metric(LOGGER, "dispatcher", "Prepared", len(replies))
    return replies
