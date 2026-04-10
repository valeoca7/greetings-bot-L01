import base64
import binascii
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


class ApiGatewayRequestError(ValueError):
    pass


@dataclass(frozen=True)
class ApiGatewayResponse:
    status_code: int
    body: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "statusCode": self.status_code,
            "headers": {
                "content-type": "application/json",
                "cache-control": "no-store",
                "x-content-type-options": "nosniff",
            },
            "body": self.body,
        }


@dataclass(frozen=True)
class ApiGatewayRequest:
    body: Optional[str]
    headers: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_event(cls, event: Mapping[str, Any]) -> "ApiGatewayRequest":
        raw_headers = event.get("headers") or {}
        if not isinstance(raw_headers, dict):
            raise ApiGatewayRequestError("request headers must be an object")
        headers = {
            str(name).lower(): str(value) for name, value in raw_headers.items()
        }
        body = event.get("body")
        if isinstance(body, str) and event.get("isBase64Encoded") is True:
            try:
                body = base64.b64decode(body, validate=True).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError) as error:
                raise ApiGatewayRequestError("invalid encoded body") from error
        return cls(
            body=body if isinstance(body, str) else None,
            headers=headers,
        )

    def json_body(self) -> Mapping[str, Any]:
        if self.body is None:
            raise ApiGatewayRequestError("request body is required")
        try:
            payload = json.loads(self.body)
        except json.JSONDecodeError as error:
            raise ApiGatewayRequestError("request body must be JSON") from error
        if not isinstance(payload, dict):
            raise ApiGatewayRequestError("request body must be an object")
        return payload
