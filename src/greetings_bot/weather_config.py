from dataclasses import dataclass
from typing import Mapping

from greetings_bot.config_values import integer_value


@dataclass(frozen=True)
class WeatherSettings:
    timeout_seconds: int = 5
    max_calls: int = 20
    cache_minutes: int = 60
    stale_hours: int = 24


def weather_settings_from_env(environ: Mapping[str, str]) -> WeatherSettings:
    return WeatherSettings(
        integer_value(environ, "WEATHER_TIMEOUT_SECONDS", 5, 1),
        integer_value(environ, "WEATHER_MAX_CALLS", 20, 1),
        integer_value(environ, "WEATHER_CACHE_MINUTES", 60, 1),
        integer_value(environ, "WEATHER_STALE_HOURS", 24, 1),
    )


def weather_timeout_from_env(environ: Mapping[str, str]) -> int:
    return integer_value(environ, "WEATHER_TIMEOUT_SECONDS", 5, 1)
