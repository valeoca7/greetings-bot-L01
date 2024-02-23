from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class WeatherLocation:
    name: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name or len(name) > 80:
            raise ValueError("location name is invalid")
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude is out of range")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude is out of range")
        object.__setattr__(self, "name", name)


@dataclass(frozen=True)
class DailyForecast:
    date: date
    low_celsius: float
    high_celsius: float
    condition: str
    precipitation_percent: int = 0

    def __post_init__(self) -> None:
        if self.low_celsius > self.high_celsius:
            raise ValueError("forecast temperatures are reversed")
        if not self.condition.strip():
            raise ValueError("forecast condition is required")
        if not 0 <= self.precipitation_percent <= 100:
            raise ValueError("precipitation percent is out of range")


class WeatherProvider(Protocol):
    def daily_forecast(
        self, location: WeatherLocation, forecast_date: date
    ) -> DailyForecast:
        ...
