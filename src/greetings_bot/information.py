from dataclasses import dataclass
from typing import Protocol, Sequence


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


def parse_information_request(arguments: Sequence[str]) -> InformationRequest:
    if not arguments:
        raise ValueError("information request kind is required")
    kind = arguments[0].lower()
    query = " ".join(arguments[1:]).strip()
    if kind in ("joke", "fact"):
        if query:
            raise ValueError("request does not accept a query")
        return InformationRequest(kind)
    if kind not in ("person", "place") or not query:
        raise ValueError("unknown or incomplete information request")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError("information query is too long")
    return InformationRequest(kind, query)
