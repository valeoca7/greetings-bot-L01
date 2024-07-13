import os
from datetime import timedelta
from typing import Callable, Mapping, Optional

from greetings_bot.clock import Clock, SystemClock
from greetings_bot.dynamo_users import DynamoTable
from greetings_bot.dynamo_weather_cache import DynamoWeatherCache
from greetings_bot.open_meteo import weather_provider_from_env
from greetings_bot.weather_cache import (
    CachingWeatherProvider,
    InMemoryWeatherCache,
    WeatherCache,
)
from greetings_bot.weather_limits import RateLimitedWeatherProvider


def reliable_weather_provider(
    environ: Mapping[str, str] = os.environ,
    table: Optional[DynamoTable] = None,
    clock: Optional[Clock] = None,
    opener: Optional[Callable] = None,
) -> CachingWeatherProvider:
    try:
        max_calls = int(environ.get("WEATHER_MAX_CALLS", "20"))
        cache_minutes = int(environ.get("WEATHER_CACHE_MINUTES", "60"))
        stale_hours = int(environ.get("WEATHER_STALE_HOURS", "24"))
    except ValueError as error:
        raise ValueError("weather reliability settings must be integers") from error
    runtime_clock = clock or SystemClock()
    upstream = RateLimitedWeatherProvider(
        weather_provider_from_env(environ, opener), max_calls, runtime_clock
    )
    cache: WeatherCache = (
        DynamoWeatherCache(table) if table is not None else InMemoryWeatherCache()
    )
    return CachingWeatherProvider(
        upstream,
        cache,
        runtime_clock,
        timedelta(minutes=cache_minutes),
        timedelta(hours=stale_hours),
    )
