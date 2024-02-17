from datetime import date
from typing import Dict

from greetings_bot.weather import WeatherLocation


FORECAST_ENDPOINT = "https://api.open-meteo.com/v1/forecast"


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
