from datetime import datetime, timedelta
from typing import Iterator
from zoneinfo import ZoneInfo

from greetings_bot.users import User


LOAD_TIMEZONES = (
    "UTC",
    "America/Vancouver",
    "America/Toronto",
    "Europe/Kyiv",
    "Asia/Tokyo",
)


def synthetic_profiles(
    count: int, current_time: datetime, due_every: int
) -> Iterator[User]:
    if count < 0 or due_every < 1:
        raise ValueError("invalid synthetic profile shape")
    for index in range(count):
        timezone_name = LOAD_TIMEZONES[index % len(LOAD_TIMEZONES)]
        local_time = current_time.astimezone(ZoneInfo(timezone_name))
        if index % due_every:
            local_time += timedelta(minutes=1)
        yield User(
            index + 1,
            index + 1,
            "User {}".format(index + 1),
            greeting_time=local_time.strftime("%H:%M"),
            timezone=timezone_name,
        )
