import logging
from datetime import datetime

from typing import Iterable, List, Optional

from greetings_bot.greetings import format_scheduled_greeting
from greetings_bot.clock import Clock
from greetings_bot.deliveries import Delivery, DeliveryLedger, InMemoryDeliveryLedger
from greetings_bot.telegram import Reply
from greetings_bot.timezones import user_local_time
from greetings_bot.users import User, UserRepository


LOGGER = logging.getLogger(__name__)


def is_greeting_due(user: User, current_time: datetime) -> bool:
    return user.greeting_time == user_local_time(user, current_time).strftime("%H:%M")


def is_delivery_day(user: User, current_time: datetime) -> bool:
    day = user_local_time(user, current_time).strftime("%a").lower()
    return day in user.greeting_days


def is_quiet_time(user: User, current_time: datetime) -> bool:
    if user.quiet_start is None or user.quiet_end is None:
        return False
    local_time = user_local_time(user, current_time).strftime("%H:%M")
    if user.quiet_start < user.quiet_end:
        return user.quiet_start <= local_time < user.quiet_end
    return local_time >= user.quiet_start or local_time < user.quiet_end


def due_users(users: Iterable[User], current_time: datetime) -> List[User]:
    return [
        user
        for user in users
        if user.enabled
        and is_delivery_day(user, current_time)
        and is_greeting_due(user, current_time)
        and not is_quiet_time(user, current_time)
    ]


def build_greeting_replies(users: Iterable[User]) -> List[Reply]:
    return [
        Reply(chat_id=user.chat_id, text=format_scheduled_greeting(user))
        for user in users
    ]


def greeting_delivery(user: User, current_time: datetime) -> Delivery:
    return Delivery(user.telegram_id, user_local_time(user, current_time).date())


class GreetingDispatcher:
    def __init__(
        self,
        users: UserRepository,
        clock: Clock,
        deliveries: Optional[DeliveryLedger] = None,
        max_batch: int = 100,
    ) -> None:
        if max_batch < 1:
            raise ValueError("max_batch must be positive")
        self.users = users
        self.clock = clock
        self.deliveries = deliveries or InMemoryDeliveryLedger()
        self.max_batch = max_batch

    def dispatch(
        self, available_users: Optional[Iterable[User]] = None
    ) -> List[Reply]:
        current_time = self.clock.now()
        if available_users is None:
            available_users = self.users.all()
        users = [
            user
            for user in due_users(available_users, current_time)
            if not self.deliveries.contains(greeting_delivery(user, current_time))
        ][: self.max_batch]
        LOGGER.info("dispatching %d scheduled greetings", len(users))
        replies = build_greeting_replies(users)
        for user in users:
            self.deliveries.record(greeting_delivery(user, current_time))
        return replies
