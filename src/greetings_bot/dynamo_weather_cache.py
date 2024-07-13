from datetime import date, datetime
from typing import Dict, Optional

from greetings_bot.dynamo_users import DynamoTable
from greetings_bot.weather import DailyForecast, WeatherLocation
from greetings_bot.weather_cache import CachedForecast


def weather_cache_key(
    location: WeatherLocation, forecast_date: date
) -> Dict[str, object]:
    return {
        "pk": "WEATHER#{}#{}".format(location.latitude, location.longitude),
        "sk": "FORECAST#{}".format(forecast_date.isoformat()),
    }


class DynamoWeatherCache:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def get(
        self, location: WeatherLocation, forecast_date: date
    ) -> Optional[CachedForecast]:
        response = self.table.get_item(
            Key=weather_cache_key(location, forecast_date)
        )
        item = response.get("Item")
        if item is None:
            return None
        try:
            forecast = DailyForecast(
                forecast_date,
                float(item["low_celsius"]),
                float(item["high_celsius"]),
                str(item["condition"]),
                int(item["precipitation_percent"]),
            )
            return CachedForecast(
                forecast, datetime.fromisoformat(str(item["stored_at"]))
            )
        except (KeyError, TypeError, ValueError):
            return None

    def put(self, location: WeatherLocation, value: CachedForecast) -> None:
        item = weather_cache_key(location, value.forecast.date)
        item.update(
            {
                "entity": "weather_forecast",
                "low_celsius": str(value.forecast.low_celsius),
                "high_celsius": str(value.forecast.high_celsius),
                "condition": value.forecast.condition,
                "precipitation_percent": value.forecast.precipitation_percent,
                "stored_at": value.stored_at.isoformat(),
                "expires_at": int(value.stored_at.timestamp()) + 172800,
            }
        )
        self.table.put_item(Item=item)
