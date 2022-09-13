from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def validate_timezone(name: str) -> str:
    value = name.strip()
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as error:
        raise ValueError("unknown timezone") from error
    return value
