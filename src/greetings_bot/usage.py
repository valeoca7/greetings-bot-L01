import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, Mapping, Tuple

from greetings_bot.observability import emit_metric


USAGE_KINDS = ("weather_calls", "information_requests", "queued_messages")
METRIC_NAMES = {
    "weather_calls": "WeatherCalls",
    "information_requests": "InformationRequests",
    "queued_messages": "QueuedMessages",
}
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsageBudgets:
    weather_calls: int = 500
    information_requests: int = 100
    queued_messages: int = 5000

    def __post_init__(self) -> None:
        for value in (
            self.weather_calls,
            self.information_requests,
            self.queued_messages,
        ):
            if not 1 <= value <= 1000000:
                raise ValueError("usage budgets must be between 1 and 1000000")

    def for_kind(self, kind: str) -> int:
        if kind not in USAGE_KINDS:
            raise ValueError("unknown usage kind")
        return int(getattr(self, kind))

    def public_snapshot(self) -> Tuple[Tuple[str, int], ...]:
        return tuple((kind, self.for_kind(kind)) for kind in USAGE_KINDS)


def usage_budgets_from_env(environ: Mapping[str, str]) -> UsageBudgets:
    try:
        return UsageBudgets(
            int(environ.get("WEATHER_DAILY_BUDGET", "500")),
            int(environ.get("INFORMATION_DAILY_BUDGET", "100")),
            int(environ.get("QUEUE_DAILY_BUDGET", "5000")),
        )
    except ValueError as error:
        raise ValueError("invalid usage budget configuration") from error


class UsageMeter:
    def __init__(self, budgets: UsageBudgets = UsageBudgets()) -> None:
        self.budgets = budgets
        self._day = None
        self._counts: Dict[str, int] = {}
        self._warned = set()

    def record(self, kind: str, amount: int, day: date) -> int:
        if kind not in USAGE_KINDS:
            raise ValueError("unknown usage kind")
        if amount < 1:
            raise ValueError("usage amount must be positive")
        if day != self._day:
            self._day = day
            self._counts = {}
            self._warned = set()
        total = self._counts.get(kind, 0) + amount
        self._counts[kind] = total
        emit_metric(LOGGER, "usage", METRIC_NAMES[kind], amount)
        if total >= self.budgets.for_kind(kind) and kind not in self._warned:
            self._warned.add(kind)
            emit_metric(LOGGER, "usage", "BudgetWarning")
        return total

    def count(self, kind: str) -> int:
        if kind not in USAGE_KINDS:
            raise ValueError("unknown usage kind")
        return self._counts.get(kind, 0)
