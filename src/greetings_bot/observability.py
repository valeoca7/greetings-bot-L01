import json
import logging
import time
from typing import Any, Mapping


SENSITIVE_FIELD_PARTS = (
    "authorization",
    "token",
    "secret",
    "body",
    "text",
    "query",
    "answer",
)


def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    payload = {"event": event}
    payload.update(_redact_mapping(fields))
    logger.log(level, json.dumps(payload, separators=(",", ":"), sort_keys=True))


def _redact_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        str(key): (
            "[redacted]"
            if any(part in str(key).lower() for part in SENSITIVE_FIELD_PARTS)
            else _redact_value(item)
        )
        for key, item in value.items()
    }


def _redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _redact_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_redact_value(item) for item in value]
    return value


def correlation_id(event: Mapping[str, Any], context: object = None) -> str:
    request_id = getattr(context, "aws_request_id", None)
    if request_id:
        return str(request_id)
    request_context = event.get("requestContext")
    if isinstance(request_context, dict) and request_context.get("requestId"):
        return str(request_context["requestId"])
    return str(event.get("id", "local"))


def emit_metric(
    logger: logging.Logger,
    service: str,
    name: str,
    value: float = 1,
    unit: str = "Count",
    timestamp_ms: int = None,
) -> None:
    payload = {
        "_aws": {
            "Timestamp": (
                timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
            ),
            "CloudWatchMetrics": [
                {
                    "Namespace": "GreetingsBot",
                    "Dimensions": [["Service"]],
                    "Metrics": [{"Name": name, "Unit": unit}],
                }
            ],
        },
        "Service": service,
        name: value,
    }
    logger.info(json.dumps(payload, separators=(",", ":"), sort_keys=True))
