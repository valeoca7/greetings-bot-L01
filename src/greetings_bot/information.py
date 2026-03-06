from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from greetings_bot.clock import Clock, SystemClock
from greetings_bot.usage import UsageMeter


MAX_QUERY_LENGTH = 120


@dataclass(frozen=True)
class InformationRequest:
    kind: str
    query: str = ""


class InformationProviderError(RuntimeError):
    pass


class InformationProvider(Protocol):
    def answer(self, request: InformationRequest) -> str:
        ...


class InformationService:
    def __init__(
        self,
        provider: InformationProvider,
        max_answer_length: int = 600,
        usage_meter: Optional[UsageMeter] = None,
        clock: Optional[Clock] = None,
    ) -> None:
        if max_answer_length < 1:
            raise ValueError("answer length must be positive")
        self.provider = provider
        self.max_answer_length = max_answer_length
        self.usage_meter = usage_meter
        self.clock = clock or SystemClock()

    def answer(self, request: InformationRequest) -> str:
        if self.usage_meter is not None:
            self.usage_meter.record(
                "information_requests", 1, self.clock.now().date()
            )
        answer = self.provider.answer(request).strip()
        if not answer:
            raise ValueError("information answer is empty")
        if len(answer) > self.max_answer_length:
            raise ValueError("information answer is too long")
        return answer


def parse_information_request(arguments: Sequence[str]) -> InformationRequest:
    if not arguments:
        raise ValueError("information request kind is required")
    kind = arguments[0].lower()
    query = " ".join(arguments[1:]).strip()
    if kind in ("joke", "fact"):
        if query:
            raise ValueError("request does not accept a query")
        return InformationRequest(kind)
    if kind not in ("person", "place", "advice") or not query:
        raise ValueError("unknown or incomplete information request")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError("information query is too long")
    return InformationRequest(kind, query)
