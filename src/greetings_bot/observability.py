import json
import logging
from typing import Any, Mapping


def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    payload = {"event": event}
    payload.update(fields)
    logger.log(level, json.dumps(payload, separators=(",", ":"), sort_keys=True))


def correlation_id(event: Mapping[str, Any], context: object = None) -> str:
    request_id = getattr(context, "aws_request_id", None)
    if request_id:
        return str(request_id)
    request_context = event.get("requestContext")
    if isinstance(request_context, dict) and request_context.get("requestId"):
        return str(request_context["requestId"])
    return str(event.get("id", "local"))
