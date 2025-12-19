from dataclasses import dataclass
from typing import Mapping, Tuple

from greetings_bot.greeting_templates import (
    ALLOWED_TEMPLATE_VARIABLES,
    TEMPLATE_CATEGORIES,
)
from greetings_bot.feature_flags import feature_flags_from_env
from greetings_bot.information_runtime import (
    DEFAULT_BEDROCK_MODEL_ID,
    information_requests_enabled,
    information_weekly_limit,
)
from greetings_bot.messages import MessageCatalog
from greetings_bot.retention import retention_from_env


@dataclass(frozen=True)
class DashboardConfig:
    information_enabled: bool
    information_weekly_limit: int
    bedrock_model: str
    weather_max_calls: int
    weather_cache_minutes: int
    weather_stale_hours: int
    delivery_admin_configured: bool
    delivery_history_days: int = 90
    delivery_receipt_days: int = 14
    supported_locales: Tuple[str, ...] = ("en", "uk")
    fallback_locale: str = "en"
    template_categories: Tuple[str, ...] = TEMPLATE_CATEGORIES
    template_variables: Tuple[str, ...] = ALLOWED_TEMPLATE_VARIABLES
    feature_flags: Tuple[Tuple[str, bool], ...] = (
        ("information_requests", False),
        ("greeting_previews", True),
        ("weather_summaries", True),
    )


def dashboard_config_from_env(environ: Mapping[str, str]) -> DashboardConfig:
    messages = MessageCatalog()
    feature_flags = feature_flags_from_env(environ)
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
    retention = retention_from_env(environ)
    return DashboardConfig(
        information_requests_enabled(environ),
        information_weekly_limit(environ),
        model,
        weather_max_calls,
        weather_cache_minutes,
        weather_stale_hours,
        delivery_configured,
        retention.delivery_days,
        retention.receipt_days,
        messages.supported_locales,
        "en",
        TEMPLATE_CATEGORIES,
        ALLOWED_TEMPLATE_VARIABLES,
        feature_flags.public_snapshot(),
    )
