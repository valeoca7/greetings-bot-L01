import re
from dataclasses import replace

from greetings_bot.users import User


TIME_PATTERN = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")


def validate_greeting_time(value: str) -> str:
    value = value.strip()
    if not TIME_PATTERN.match(value):
        raise ValueError("time must use HH:MM in 24-hour format")
    return value


def set_greeting_time(user: User, value: str) -> User:
    return replace(user, greeting_time=validate_greeting_time(value))
