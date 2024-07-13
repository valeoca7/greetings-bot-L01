import logging
from datetime import date, datetime, timedelta
from typing import Optional

from greetings_bot.clock import Clock, SystemClock
from greetings_bot.observability import emit_metric
from greetings_bot.weather import (
    DailyForecast,
    WeatherLocation,
    WeatherProvider,
    WeatherProviderError,
)


LOGGER = logging.getLogger(__name__)


class RateLimitedWeatherProvider:
    def __init__(
        self,
        upstream: WeatherProvider,
        max_calls: int = 20,
        clock: Clock = None,
        window: timedelta = timedelta(minutes=1),
    ) -> None:
        if max_calls < 1:
            raise ValueError("weather call limit must be positive")
        if window <= timedelta(0):
            raise ValueError("weather call window must be positive")
        self.upstream = upstream
        self.max_calls = max_calls
        self.clock = clock or SystemClock()
        self.window = window
        self.calls = 0
        self.window_started: Optional[datetime] = None

    def daily_forecast(
        self, location: WeatherLocation, forecast_date: date
    ) -> DailyForecast:
        now = self.clock.now()
        if (
            self.window_started is None
            or now - self.window_started >= self.window
        ):
            self.window_started = now
            self.calls = 0
        if self.calls >= self.max_calls:
            emit_metric(LOGGER, "weather", "RateLimited")
            raise WeatherProviderError("weather provider call limit reached")
        self.calls += 1
        return self.upstream.daily_forecast(location, forecast_date)
