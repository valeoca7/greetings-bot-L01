import base64
from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class ApiGatewayRequest:
    body: Optional[str]

    @classmethod
    def from_event(cls, event: Mapping[str, Any]) -> "ApiGatewayRequest":
        body = event.get("body")
        if isinstance(body, str) and event.get("isBase64Encoded") is True:
            body = base64.b64decode(body).decode("utf-8")
        return cls(body=body if isinstance(body, str) else None)
