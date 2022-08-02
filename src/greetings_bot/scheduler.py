from datetime import datetime

from greetings_bot.users import User


def is_greeting_due(user: User, current_time: datetime) -> bool:
    return user.greeting_time == current_time.strftime("%H:%M")
