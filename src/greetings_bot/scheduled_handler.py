from typing import Any, Dict, List, Mapping, Optional

from greetings_bot.clock import FixedClock
from greetings_bot.deliveries import DeliveryLedger
from greetings_bot.scheduled_event import event_time
from greetings_bot.scheduler import GreetingDispatcher
from greetings_bot.telegram import reply_batch
from greetings_bot.users import UserRepository


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

    def handle(self, event: Mapping[str, Any]) -> List[Dict[str, object]]:
        dispatcher = GreetingDispatcher(
            self.users,
            FixedClock(event_time(event)),
            self.deliveries,
            self.max_batch,
        )
        return reply_batch(dispatcher.dispatch())
