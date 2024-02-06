from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class WeatherLocation:
    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class DailyForecast:
    date: date
    low_celsius: float
    high_celsius: float
    condition: str
    precipitation_percent: int = 0


class WeatherProvider(Protocol):
    def daily_forecast(
        self, location: WeatherLocation, forecast_date: date
    ) -> DailyForecast:
        ...
