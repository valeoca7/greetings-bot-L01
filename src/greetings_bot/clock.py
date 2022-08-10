from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now()


class FixedClock:
    def __init__(self, current_time: datetime) -> None:
        self.current_time = current_time

    def now(self) -> datetime:
        return self.current_time
