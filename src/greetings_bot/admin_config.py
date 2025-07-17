from dataclasses import dataclass
from typing import Mapping

from greetings_bot.information_runtime import (
    DEFAULT_BEDROCK_MODEL_ID,
    information_requests_enabled,
    information_weekly_limit,
)


@dataclass(frozen=True)
class DashboardConfig:
    information_enabled: bool
    information_weekly_limit: int
    bedrock_model: str
    weather_max_calls: int
    weather_cache_minutes: int
    weather_stale_hours: int
    delivery_admin_configured: bool


def dashboard_config_from_env(environ: Mapping[str, str]) -> DashboardConfig:
    model = environ.get("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID).strip()
    if not model:
        raise ValueError("BEDROCK_MODEL_ID must not be blank")
    try:
        weather_max_calls = int(environ.get("WEATHER_MAX_CALLS", "20"))
        weather_cache_minutes = int(environ.get("WEATHER_CACHE_MINUTES", "60"))
        weather_stale_hours = int(environ.get("WEATHER_STALE_HOURS", "24"))
    except ValueError as error:
        raise ValueError("weather settings must be integers") from error
    if min(weather_max_calls, weather_cache_minutes, weather_stale_hours) < 1:
        raise ValueError("weather settings must be positive")
    queue_names = (
        "DELIVERY_QUEUE_URL",
        "DELIVERY_DLQ_URL",
        "DELIVERY_QUEUE_ARN",
        "DELIVERY_DLQ_ARN",
    )
    delivery_configured = all(environ.get(name, "").strip() for name in queue_names)
    return DashboardConfig(
        information_requests_enabled(environ),
        information_weekly_limit(environ),
        model,
        weather_max_calls,
        weather_cache_minutes,
        weather_stale_hours,
        delivery_configured,
    )
