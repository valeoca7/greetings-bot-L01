import re


TIME_PATTERN = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")


def validate_greeting_time(value: str) -> str:
    value = value.strip()
    if not TIME_PATTERN.match(value):
        raise ValueError("time must use HH:MM in 24-hour format")
    return value
