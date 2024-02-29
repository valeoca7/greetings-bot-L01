import os
from datetime import date
from typing import Callable, Dict, Mapping, Optional, Protocol

from greetings_bot.weather import (
    DailyForecast,
    WeatherLocation,
    WeatherProviderError,
)
from greetings_bot.weather_client import JsonHttpClient


FORECAST_ENDPOINT = "https://api.open-meteo.com/v1/forecast"


class JsonClient(Protocol):
    def get(
        self, endpoint: str, params: Mapping[str, object]
    ) -> Mapping[str, object]:
        ...


def weather_condition(code: int) -> str:
    if code == 0:
        return "clear"
    if code in (1, 2):
        return "partly cloudy"
    if code == 3:
        return "overcast"
    if code in (45, 48):
        return "fog"
    if 51 <= code <= 57:
        return "drizzle"
    if 61 <= code <= 67 or 80 <= code <= 82:
        return "rain"
    if 71 <= code <= 77 or 85 <= code <= 86:
        return "snow"
    if 95 <= code <= 99:
        return "thunderstorm"
    return "unknown conditions"


def forecast_params(
    location: WeatherLocation, forecast_date: date
) -> Dict[str, object]:
    day = forecast_date.isoformat()
    return {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "daily": (
            "temperature_2m_min,temperature_2m_max,"
            "precipitation_probability_max,weather_code"
        ),
        "timezone": "auto",
        "start_date": day,
        "end_date": day,
    }


class OpenMeteoWeatherProvider:
    def __init__(self, client: JsonClient = None) -> None:
        self.client = client or JsonHttpClient()

    def daily_forecast(
        self, location: WeatherLocation, forecast_date: date
    ) -> DailyForecast:
        try:
            value = self.client.get(
                FORECAST_ENDPOINT, forecast_params(location, forecast_date)
            )
            daily = value["daily"]
            index = daily["time"].index(forecast_date.isoformat())
            return DailyForecast(
                forecast_date,
                float(daily["temperature_2m_min"][index]),
                float(daily["temperature_2m_max"][index]),
                weather_condition(int(daily["weather_code"][index])),
                int(daily["precipitation_probability_max"][index] or 0),
            )
        except (
            AttributeError,
            KeyError,
            IndexError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as error:
            raise WeatherProviderError("weather provider unavailable") from error


def weather_provider_from_env(
    environ: Mapping[str, str] = os.environ,
    opener: Optional[Callable] = None,
) -> OpenMeteoWeatherProvider:
    try:
        timeout = int(environ.get("WEATHER_TIMEOUT_SECONDS", "5"))
    except ValueError:
        raise ValueError("weather timeout must be an integer")
    client = JsonHttpClient(timeout=timeout)
    if opener is not None:
        client = JsonHttpClient(opener, timeout)
    return OpenMeteoWeatherProvider(client)
