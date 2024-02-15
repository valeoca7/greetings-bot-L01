from datetime import date
from typing import Dict

from greetings_bot.weather import WeatherLocation


FORECAST_ENDPOINT = "https://api.open-meteo.com/v1/forecast"


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
