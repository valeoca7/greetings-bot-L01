from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from greetings_bot.greeting_templates import (
    ALLOWED_TEMPLATE_VARIABLES,
    TEMPLATE_CATEGORIES,
)
from greetings_bot.information_runtime import (
    bedrock_model_id,
)
from greetings_bot.messages import MessageCatalog
from greetings_bot.startup_diagnostics import (
    RuntimeConfiguration,
    runtime_configuration_from_env,
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
    dispatch_batch_size: int = 100
    queue_high_watermark: int = 1000
    profile_page_size: int = 100
    usage_budgets: Tuple[Tuple[str, int], ...] = (
        ("weather_calls", 500),
        ("information_requests", 100),
        ("queued_messages", 5000),
    )


def dashboard_config_from_env(
    environ: Mapping[str, str],
    runtime: Optional[RuntimeConfiguration] = None,
) -> DashboardConfig:
    messages = MessageCatalog()
    runtime = runtime or runtime_configuration_from_env(environ)
    feature_flags = runtime.feature_flags
    model = bedrock_model_id(environ)
    weather = runtime.weather
    queue_names = (
        "DELIVERY_QUEUE_URL",
        "DELIVERY_DLQ_URL",
        "DELIVERY_QUEUE_ARN",
        "DELIVERY_DLQ_ARN",
    )
    delivery_configured = all(environ.get(name, "").strip() for name in queue_names)
    retention = runtime.retention
    throughput = runtime.throughput
    usage_budgets = runtime.usage_budgets
    return DashboardConfig(
        feature_flags.enabled("information_requests"),
        runtime.information_weekly_limit,
        model,
        weather.max_calls,
        weather.cache_minutes,
        weather.stale_hours,
        delivery_configured,
        retention.delivery_days,
        retention.receipt_days,
        messages.supported_locales,
        "en",
        TEMPLATE_CATEGORIES,
        ALLOWED_TEMPLATE_VARIABLES,
        feature_flags.public_snapshot(),
        throughput.dispatch_batch_size,
        throughput.queue_high_watermark,
        throughput.profile_page_size,
        usage_budgets.public_snapshot(),
    )
