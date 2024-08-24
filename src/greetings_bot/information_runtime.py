import os
from typing import Mapping


def information_requests_enabled(
    environ: Mapping[str, str] = os.environ,
) -> bool:
    value = environ.get("INFO_REQUESTS_ENABLED", "false").lower()
    if value not in ("true", "false"):
        raise ValueError("INFO_REQUESTS_ENABLED must be true or false")
    return value == "true"
