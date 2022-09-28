from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from greetings_bot.users import User


def validate_timezone(name: str) -> str:
    value = name.strip()
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as error:
        raise ValueError("unknown timezone") from error
    return value


def user_local_time(user: User, current_time: datetime) -> datetime:
    return current_time.astimezone(ZoneInfo(user.timezone))
