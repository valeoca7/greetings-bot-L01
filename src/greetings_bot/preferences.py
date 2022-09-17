import re
from dataclasses import replace

from greetings_bot.timezones import validate_timezone
from greetings_bot.users import User, normalize_first_name


TIME_PATTERN = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
MAX_NAME_LENGTH = 40


def validate_greeting_time(value: str) -> str:
    value = value.strip()
    if not TIME_PATTERN.match(value):
        raise ValueError("time must use HH:MM in 24-hour format")
    return value


def set_greeting_time(user: User, value: str) -> User:
    return replace(user, greeting_time=validate_greeting_time(value))


def set_first_name(user: User, value: str) -> User:
    first_name = normalize_first_name(value)
    if len(first_name) > MAX_NAME_LENGTH:
        raise ValueError("name is too long")
    return replace(user, first_name=first_name)


def set_timezone(user: User, value: str) -> User:
    return replace(user, timezone=validate_timezone(value))
