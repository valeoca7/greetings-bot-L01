import json
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional
from urllib.parse import parse_qs


class AdminRequestError(ValueError):
    pass


@dataclass(frozen=True)
class AdminRequest:
    method: str
    path: str
    headers: Mapping[str, str]
    query: Mapping[str, str] = field(default_factory=dict)
    body: Optional[str] = None

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
        raw_query = event.get("queryStringParameters") or {}
        if not isinstance(raw_query, dict):
            raise AdminRequestError("admin query parameters must be an object")
        body = event.get("body")
        if body is not None and not isinstance(body, str):
            raise AdminRequestError("admin body must be text")
        if event.get("isBase64Encoded"):
            raise AdminRequestError("encoded admin bodies are not supported")
        headers = {
            str(name).lower(): str(value)
            for name, value in raw_headers.items()
        }
        query = {str(name): str(value) for name, value in raw_query.items()}
        return cls(method.upper(), path, headers, query, body)

    def json_body(self) -> Mapping[str, object]:
        try:
            value = json.loads(self.body or "{}")
        except json.JSONDecodeError as error:
            raise AdminRequestError("admin body must be valid JSON") from error
        if not isinstance(value, dict):
            raise AdminRequestError("admin body must be a JSON object")
        return value

    def form_body(self) -> Mapping[str, str]:
        content_type = self.headers.get("content-type", "")
        if content_type.split(";", 1)[0].strip().lower() != (
            "application/x-www-form-urlencoded"
        ):
            raise AdminRequestError("admin body must be form encoded")
        values = parse_qs(self.body or "", keep_blank_values=True)
        if any(len(items) != 1 for items in values.values()):
            raise AdminRequestError("admin form fields must be unique")
        return {name: items[0] for name, items in values.items()}


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


@dataclass(frozen=True)
class HtmlResponse:
    status_code: int
    body: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "statusCode": self.status_code,
            "headers": {
                "content-type": "text/html; charset=utf-8",
                "cache-control": "no-store",
                "content-security-policy": (
                    "default-src 'none'; style-src 'unsafe-inline'; "
                    "img-src 'self'; base-uri 'none'; frame-ancestors 'none'; "
                    "form-action 'self'"
                ),
                "referrer-policy": "no-referrer",
                "x-content-type-options": "nosniff",
                "x-frame-options": "DENY",
            },
            "body": self.body,
        }
