import unittest
from datetime import date, datetime, timezone

from greetings_bot.dynamo_weather_cache import DynamoWeatherCache, weather_cache_key
from greetings_bot.weather import DailyForecast, WeatherLocation
from greetings_bot.weather_cache import CachedForecast


class FakeTable:
    def __init__(self):
        self.items = {}

    def get_item(self, *, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {} if item is None else {"Item": item}

    def put_item(self, *, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}


class DynamoWeatherCacheTest(unittest.TestCase):
    def test_round_trips_cached_forecast(self):
        table = FakeTable()
        cache = DynamoWeatherCache(table)
        location = WeatherLocation("Vancouver", 49.2, -123.1)
        value = CachedForecast(
            DailyForecast(date(2024, 6, 20), 4.5, 12.1, "rain", 80),
            datetime(2024, 6, 20, 16, 30, tzinfo=timezone.utc),
        )

        cache.put(location, value)

        self.assertEqual(cache.get(location, value.forecast.date), value)
        item = next(iter(table.items.values()))
        self.assertEqual(item["low_celsius"], "4.5")
        self.assertGreater(item["expires_at"], 0)

    def test_returns_none_for_missing_entry(self):
        cache = DynamoWeatherCache(FakeTable())

        value = cache.get(
            WeatherLocation("Vancouver", 49.2, -123.1),
            date(2024, 6, 20),
        )

        self.assertIsNone(value)

    def test_uses_coordinates_and_date_in_key(self):
        key = weather_cache_key(
            WeatherLocation("Vancouver", 49.2, -123.1),
            date(2024, 6, 20),
        )

        self.assertEqual(key["pk"], "WEATHER#49.2#-123.1")
        self.assertEqual(key["sk"], "FORECAST#2024-06-20")

    def test_ignores_malformed_cached_item(self):
        table = FakeTable()
        location = WeatherLocation("Vancouver", 49.2, -123.1)
        key = weather_cache_key(location, date(2024, 6, 20))
        table.put_item(Item={**key, "condition": "rain"})

        value = DynamoWeatherCache(table).get(location, date(2024, 6, 20))

        self.assertIsNone(value)


if __name__ == "__main__":
    unittest.main()
