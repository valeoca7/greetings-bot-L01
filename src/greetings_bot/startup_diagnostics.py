import logging
from dataclasses import dataclass
from typing import Dict, Mapping

from greetings_bot.feature_flags import FeatureFlags, feature_flags_from_env
from greetings_bot.information_runtime import (
    bedrock_timeout_seconds,
    information_weekly_limit,
)
from greetings_bot.observability import log_event
from greetings_bot.retention import RetentionPolicy, retention_from_env
from greetings_bot.throughput import ThroughputPolicy, throughput_from_env
from greetings_bot.usage import UsageBudgets, usage_budgets_from_env
from greetings_bot.weather_config import WeatherSettings, weather_settings_from_env


@dataclass(frozen=True)
class RuntimeConfiguration:
    feature_flags: FeatureFlags
    throughput: ThroughputPolicy
    retention: RetentionPolicy
    usage_budgets: UsageBudgets
    weather: WeatherSettings
    information_weekly_limit: int
    bedrock_timeout_seconds: int

    def public_snapshot(self) -> Dict[str, object]:
        values: Dict[str, object] = dict(self.feature_flags.public_snapshot())
        values.update(
            {
                "information_weekly_limit": self.information_weekly_limit,
                "bedrock_timeout_seconds": self.bedrock_timeout_seconds,
                "weather_timeout_seconds": self.weather.timeout_seconds,
                "weather_max_calls": self.weather.max_calls,
                "weather_cache_minutes": self.weather.cache_minutes,
                "weather_stale_hours": self.weather.stale_hours,
                "dispatch_batch_size": self.throughput.dispatch_batch_size,
                "queue_high_watermark": self.throughput.queue_high_watermark,
                "profile_page_size": self.throughput.profile_page_size,
                "delivery_history_days": self.retention.delivery_days,
                "delivery_receipt_days": self.retention.receipt_days,
                "weather_daily_budget": self.usage_budgets.weather_calls,
                "information_daily_budget": self.usage_budgets.information_requests,
                "queue_daily_budget": self.usage_budgets.queued_messages,
            }
        )
        return values


def runtime_configuration_from_env(
    environ: Mapping[str, str],
) -> RuntimeConfiguration:
    return RuntimeConfiguration(
        feature_flags_from_env(environ),
        throughput_from_env(environ),
        retention_from_env(environ),
        usage_budgets_from_env(environ),
        weather_settings_from_env(environ),
        information_weekly_limit(environ),
        bedrock_timeout_seconds(environ),
    )


def startup_diagnostics_from_env(
    environ: Mapping[str, str],
) -> Dict[str, object]:
    return runtime_configuration_from_env(environ).public_snapshot()


def log_startup_diagnostics(
    logger: logging.Logger, configuration: RuntimeConfiguration
) -> None:
    log_event(logger, "configuration_loaded", **configuration.public_snapshot())
