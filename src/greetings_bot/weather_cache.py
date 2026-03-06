import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Optional, Protocol, Tuple

from greetings_bot.weather import DailyForecast, WeatherLocation
from greetings_bot.weather import WeatherProvider, WeatherProviderError
from greetings_bot.clock import Clock
from greetings_bot.observability import emit_metric
from greetings_bot.usage import UsageMeter


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CachedForecast:
    forecast: DailyForecast
    stored_at: datetime


class WeatherCache(Protocol):
    def get(
        self, location: WeatherLocation, forecast_date: date
    ) -> Optional[CachedForecast]:
        ...

    def put(self, location: WeatherLocation, value: CachedForecast) -> None:
        ...


CacheKey = Tuple[float, float, date]


class InMemoryWeatherCache:
    def __init__(self) -> None:
        self.values: Dict[CacheKey, CachedForecast] = {}

    @staticmethod
    def key(location: WeatherLocation, forecast_date: date) -> CacheKey:
        return (location.latitude, location.longitude, forecast_date)

    def get(
        self, location: WeatherLocation, forecast_date: date
    ) -> Optional[CachedForecast]:
        return self.values.get(self.key(location, forecast_date))

    def put(self, location: WeatherLocation, value: CachedForecast) -> None:
        self.values[self.key(location, value.forecast.date)] = value


class CachingWeatherProvider:
    def __init__(
        self,
        upstream: WeatherProvider,
        cache: WeatherCache,
        clock: Clock,
        fresh_for: timedelta = timedelta(hours=1),
        stale_for: timedelta = timedelta(hours=24),
        usage_meter: Optional[UsageMeter] = None,
    ) -> None:
        if fresh_for <= timedelta(0) or stale_for < fresh_for:
            raise ValueError("invalid weather cache windows")
        self.upstream = upstream
        self.cache = cache
        self.clock = clock
        self.fresh_for = fresh_for
        self.stale_for = stale_for
        self.usage_meter = usage_meter

    def daily_forecast(
        self, location: WeatherLocation, forecast_date: date
    ) -> DailyForecast:
        cached = self.cache.get(location, forecast_date)
        now = self.clock.now()
        age = None if cached is None else now - cached.stored_at
        if cached is not None and age <= self.fresh_for:
            emit_metric(LOGGER, "weather", "CacheHit")
            return cached.forecast
        emit_metric(LOGGER, "weather", "CacheMiss")
        try:
            emit_metric(LOGGER, "weather", "ProviderCall")
            if self.usage_meter is not None:
                self.usage_meter.record("weather_calls", 1, now.date())
            forecast = self.upstream.daily_forecast(location, forecast_date)
        except WeatherProviderError:
            emit_metric(LOGGER, "weather", "ProviderError")
            if cached is not None and age <= self.stale_for:
                emit_metric(LOGGER, "weather", "StaleFallback")
                return cached.forecast
            raise
        self.cache.put(location, CachedForecast(forecast, now))
        return forecast
