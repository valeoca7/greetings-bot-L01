import re
from dataclasses import replace
from typing import Sequence

from greetings_bot.timezones import validate_timezone
from greetings_bot.users import (
    EVERY_DAY,
    User,
    normalize_first_name,
    normalize_locale,
)
from greetings_bot.weather import WeatherLocation


TIME_PATTERN = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
MAX_NAME_LENGTH = 40
DAY_NAMES = {
    "mon": "mon", "monday": "mon",
    "tue": "tue", "tuesday": "tue",
    "wed": "wed", "wednesday": "wed",
    "thu": "thu", "thursday": "thu",
    "fri": "fri", "friday": "fri",
    "sat": "sat", "saturday": "sat",
    "sun": "sun", "sunday": "sun",
}


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


def set_locale(
    user: User,
    value: str,
    supported: Sequence[str] = ("en", "uk"),
) -> User:
    locale = normalize_locale(value)
    if locale not in supported:
        raise ValueError("unsupported locale")
    return replace(user, locale=locale)


def set_quiet_hours(user: User, start: str, end: str) -> User:
    quiet_start = validate_greeting_time(start)
    quiet_end = validate_greeting_time(end)
    if quiet_start == quiet_end:
        raise ValueError("quiet hours must have different bounds")
    return replace(user, quiet_start=quiet_start, quiet_end=quiet_end)


def clear_quiet_hours(user: User) -> User:
    return replace(user, quiet_start=None, quiet_end=None)


def set_greeting_days(user: User, values: Sequence[str]) -> User:
    if len(values) == 1 and values[0].lower() == "weekdays":
        return replace(user, greeting_days=EVERY_DAY[:5])
    if len(values) == 1 and values[0].lower() in ("daily", "everyday"):
        return replace(user, greeting_days=EVERY_DAY)
    try:
        selected = {DAY_NAMES[value.lower()] for value in values}
    except KeyError:
        raise ValueError("unknown weekday")
    if not selected:
        raise ValueError("at least one weekday is required")
    return replace(
        user,
        greeting_days=tuple(day for day in EVERY_DAY if day in selected),
    )


def set_digest_mode(user: User, value: str) -> User:
    mode = value.lower()
    if mode not in ("off", "daily"):
        raise ValueError("digest mode must be off or daily")
    return replace(user, digest_mode=mode)


def set_weather_location(
    user: User, name: str, latitude: str, longitude: str
) -> User:
    try:
        location = WeatherLocation(name, float(latitude), float(longitude))
    except ValueError as error:
        raise ValueError("invalid weather location") from error
    return replace(user, weather_location=location)


def clear_weather_location(user: User) -> User:
    return replace(user, weather_location=None, weather_summary=False)


def set_weather_units(user: User, value: str) -> User:
    units = value.lower()
    if units not in ("metric", "imperial"):
        raise ValueError("weather units must be metric or imperial")
    return replace(user, weather_units=units)


def set_weather_summary(user: User, enabled: bool) -> User:
    digest_mode = "daily" if enabled else user.digest_mode
    return replace(
        user, weather_summary=enabled, digest_mode=digest_mode
    )
