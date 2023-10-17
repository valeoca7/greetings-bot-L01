import json
import logging
from typing import Any


def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    payload = {"event": event}
    payload.update(fields)
    logger.log(level, json.dumps(payload, separators=(",", ":"), sort_keys=True))
