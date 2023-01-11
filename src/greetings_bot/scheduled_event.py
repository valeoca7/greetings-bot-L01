from datetime import datetime
from typing import Any, Mapping


class ScheduledEventError(ValueError):
    pass


def event_time(event: Mapping[str, Any]) -> datetime:
    value = event.get("time")
    if not isinstance(value, str):
        raise ScheduledEventError("scheduled event time is required")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ScheduledEventError("invalid scheduled event time") from error
