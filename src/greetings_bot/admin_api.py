import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping


class AdminRequestError(ValueError):
    pass


@dataclass(frozen=True)
class AdminRequest:
    method: str
    path: str
    headers: Mapping[str, str]

    @classmethod
    def from_event(cls, event: Mapping[str, Any]) -> "AdminRequest":
        context = event.get("requestContext", {})
        http = context.get("http", {}) if isinstance(context, dict) else {}
        method = http.get("method") or event.get("httpMethod")
        path = event.get("rawPath") or event.get("path")
        if not isinstance(method, str) or not isinstance(path, str):
            raise AdminRequestError("admin method and path are required")
        raw_headers = event.get("headers") or {}
        if not isinstance(raw_headers, dict):
            raise AdminRequestError("admin headers must be an object")
        headers = {
            str(name).lower(): str(value)
            for name, value in raw_headers.items()
        }
        return cls(method.upper(), path, headers)


@dataclass(frozen=True)
class AdminResponse:
    status_code: int
    body: Mapping[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "statusCode": self.status_code,
            "headers": {
                "content-type": "application/json",
                "cache-control": "no-store",
                "x-content-type-options": "nosniff",
            },
            "body": json.dumps(self.body, separators=(",", ":")),
        }
