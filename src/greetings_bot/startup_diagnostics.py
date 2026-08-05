import logging
from typing import Dict, Mapping

from greetings_bot.feature_flags import feature_flags_from_env
from greetings_bot.information_runtime import (
    bedrock_timeout_seconds,
    information_weekly_limit,
)
from greetings_bot.observability import log_event
from greetings_bot.retention import retention_from_env
from greetings_bot.throughput import throughput_from_env
from greetings_bot.usage import usage_budgets_from_env
from greetings_bot.weather_config import weather_settings_from_env


def startup_diagnostics_from_env(
    environ: Mapping[str, str],
) -> Dict[str, object]:
    flags = feature_flags_from_env(environ)
    throughput = throughput_from_env(environ)
    retention = retention_from_env(environ)
    budgets = usage_budgets_from_env(environ)
    weather = weather_settings_from_env(environ)
    values: Dict[str, object] = dict(flags.public_snapshot())
    values.update(
        {
            "information_weekly_limit": information_weekly_limit(environ),
            "bedrock_timeout_seconds": bedrock_timeout_seconds(environ),
            "weather_timeout_seconds": weather.timeout_seconds,
            "weather_max_calls": weather.max_calls,
            "weather_cache_minutes": weather.cache_minutes,
            "weather_stale_hours": weather.stale_hours,
            "dispatch_batch_size": throughput.dispatch_batch_size,
            "queue_high_watermark": throughput.queue_high_watermark,
            "profile_page_size": throughput.profile_page_size,
            "delivery_history_days": retention.delivery_days,
            "delivery_receipt_days": retention.receipt_days,
            "weather_daily_budget": budgets.weather_calls,
            "information_daily_budget": budgets.information_requests,
            "queue_daily_budget": budgets.queued_messages,
        }
    )
    return values


def log_startup_diagnostics(
    logger: logging.Logger, environ: Mapping[str, str]
) -> None:
    log_event(
        logger,
        "configuration_loaded",
        **startup_diagnostics_from_env(environ),
    )
