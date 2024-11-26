from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, Protocol, Tuple


@dataclass(frozen=True)
class WeeklyWindow:
    key: str
    resets_at: datetime


@dataclass(frozen=True)
class QuotaDecision:
    allowed: bool
    remaining: int
    resets_at: datetime


class InformationQuota(Protocol):
    def consume(
        self, telegram_id: int, current_time: datetime, limit: int
    ) -> QuotaDecision:
        ...


class InformationQuotaError(RuntimeError):
    pass


def weekly_window(current_time: datetime) -> WeeklyWindow:
    if current_time.tzinfo is None:
        raise ValueError("quota time must include a timezone")
    current_time = current_time.astimezone(timezone.utc)
    iso_year, iso_week, _ = current_time.isocalendar()
    next_monday = current_time.date() + timedelta(
        days=7 - current_time.weekday()
    )
    return WeeklyWindow(
        "{}-W{:02d}".format(iso_year, iso_week),
        datetime.combine(next_monday, datetime.min.time(), timezone.utc),
    )


class InMemoryInformationQuota:
    def __init__(self) -> None:
        self._counts: Dict[Tuple[int, str], int] = {}
        self._lock = Lock()

    def consume(
        self, telegram_id: int, current_time: datetime, limit: int
    ) -> QuotaDecision:
        if limit < 1:
            raise ValueError("weekly information limit must be positive")
        window = weekly_window(current_time)
        key = (telegram_id, window.key)
        with self._lock:
            used = self._counts.get(key, 0)
            if used >= limit:
                return QuotaDecision(False, 0, window.resets_at)
            used += 1
            self._counts[key] = used
        return QuotaDecision(True, limit - used, window.resets_at)
