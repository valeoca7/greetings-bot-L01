from datetime import datetime

from typing import Iterable, List

from greetings_bot.users import User


def is_greeting_due(user: User, current_time: datetime) -> bool:
    return user.greeting_time == current_time.strftime("%H:%M")


def due_users(users: Iterable[User], current_time: datetime) -> List[User]:
    return [
        user
        for user in users
        if user.enabled and is_greeting_due(user, current_time)
    ]
