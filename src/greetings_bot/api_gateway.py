from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class ApiGatewayRequest:
    body: Optional[str]

    @classmethod
    def from_event(cls, event: Mapping[str, Any]) -> "ApiGatewayRequest":
        body = event.get("body")
        return cls(body=body if isinstance(body, str) else None)
