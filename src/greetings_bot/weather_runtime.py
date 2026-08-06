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
from greetings_bot.usage import UsageMeter
from greetings_bot.weather_config import WeatherSettings, weather_settings_from_env


def reliable_weather_provider(
    environ: Mapping[str, str] = os.environ,
    table: Optional[DynamoTable] = None,
    clock: Optional[Clock] = None,
    opener: Optional[Callable] = None,
    usage_meter: Optional[UsageMeter] = None,
    settings: Optional[WeatherSettings] = None,
) -> CachingWeatherProvider:
    settings = settings or weather_settings_from_env(environ)
    runtime_clock = clock or SystemClock()
    upstream = RateLimitedWeatherProvider(
        weather_provider_from_env(environ, opener), settings.max_calls, runtime_clock
    )
    cache: WeatherCache = (
        DynamoWeatherCache(table) if table is not None else InMemoryWeatherCache()
    )
    return CachingWeatherProvider(
        upstream,
        cache,
        runtime_clock,
        timedelta(minutes=settings.cache_minutes),
        timedelta(hours=settings.stale_hours),
        usage_meter,
    )
