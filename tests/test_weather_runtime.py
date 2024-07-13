import unittest
from datetime import datetime, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.dynamo_weather_cache import DynamoWeatherCache
from greetings_bot.weather_cache import CachingWeatherProvider, InMemoryWeatherCache
from greetings_bot.weather_limits import RateLimitedWeatherProvider
from greetings_bot.weather_runtime import reliable_weather_provider


class WeatherRuntimeTest(unittest.TestCase):
    def test_builds_in_memory_reliable_provider(self):
        provider = reliable_weather_provider(
            {"WEATHER_MAX_CALLS": "7"},
            clock=FixedClock(datetime(2024, 6, 26, tzinfo=timezone.utc)),
        )

        self.assertIsInstance(provider, CachingWeatherProvider)
        self.assertIsInstance(provider.cache, InMemoryWeatherCache)
        self.assertIsInstance(provider.upstream, RateLimitedWeatherProvider)
        self.assertEqual(provider.upstream.max_calls, 7)

    def test_uses_shared_dynamo_table_when_available(self):
        table = object()

        provider = reliable_weather_provider({}, table=table)

        self.assertIsInstance(provider.cache, DynamoWeatherCache)
        self.assertIs(provider.cache.table, table)

    def test_rejects_invalid_reliability_configuration(self):
        for environ in (
            {"WEATHER_MAX_CALLS": "many"},
            {"WEATHER_CACHE_MINUTES": "0"},
            {"WEATHER_STALE_HOURS": "0"},
        ):
            with self.subTest(environ=environ):
                with self.assertRaises(ValueError):
                    reliable_weather_provider(environ)


if __name__ == "__main__":
    unittest.main()
