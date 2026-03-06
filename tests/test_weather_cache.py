import unittest
from datetime import date, datetime, timedelta, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.weather import (
    DailyForecast,
    WeatherLocation,
    WeatherProviderError,
)
from greetings_bot.weather_cache import (
    CachedForecast,
    CachingWeatherProvider,
    InMemoryWeatherCache,
)
from greetings_bot.usage import UsageMeter


class FakeProvider:
    def __init__(self, forecast=None, error=None):
        self.forecast = forecast
        self.error = error
        self.calls = 0

    def daily_forecast(self, location, forecast_date):
        self.calls += 1
        if self.error:
            raise self.error
        return self.forecast


class WeatherCacheTest(unittest.TestCase):
    def setUp(self):
        self.location = WeatherLocation("Vancouver", 49.2, -123.1)
        self.forecast = DailyForecast(
            date(2024, 6, 10), 5, 12, "cloudy", 20
        )
        self.now = datetime(2024, 6, 10, 16, 0, tzinfo=timezone.utc)

    def test_stores_forecast_by_coordinates_and_date(self):
        cache = InMemoryWeatherCache()
        location = WeatherLocation("Vancouver", 49.2, -123.1)
        forecast = DailyForecast(date(2024, 6, 10), 5, 12, "cloudy", 20)
        value = CachedForecast(
            forecast, datetime(2024, 6, 10, 16, 0, tzinfo=timezone.utc)
        )

        cache.put(location, value)

        self.assertEqual(cache.get(location, forecast.date), value)

    def test_does_not_mix_locations(self):
        cache = InMemoryWeatherCache()
        forecast = DailyForecast(date(2024, 6, 10), 5, 12, "cloudy", 20)
        cache.put(
            WeatherLocation("Vancouver", 49.2, -123.1),
            CachedForecast(
                forecast,
                datetime(2024, 6, 10, 16, 0, tzinfo=timezone.utc),
            ),
        )

        value = cache.get(
            WeatherLocation("Victoria", 48.4, -123.3), forecast.date
        )

        self.assertIsNone(value)

    def test_returns_a_fresh_cached_forecast(self):
        cache = InMemoryWeatherCache()
        cache.put(
            self.location,
            CachedForecast(self.forecast, self.now - timedelta(minutes=30)),
        )
        upstream = FakeProvider()
        provider = CachingWeatherProvider(
            upstream, cache, FixedClock(self.now)
        )

        value = provider.daily_forecast(self.location, self.forecast.date)

        self.assertEqual(value, self.forecast)
        self.assertEqual(upstream.calls, 0)

    def test_refreshes_an_expired_forecast(self):
        cache = InMemoryWeatherCache()
        cache.put(
            self.location,
            CachedForecast(self.forecast, self.now - timedelta(hours=2)),
        )
        updated = DailyForecast(self.forecast.date, 6, 13, "rain", 70)
        upstream = FakeProvider(updated)
        provider = CachingWeatherProvider(
            upstream, cache, FixedClock(self.now)
        )

        value = provider.daily_forecast(self.location, self.forecast.date)

        self.assertEqual(value, updated)
        self.assertEqual(cache.get(self.location, self.forecast.date).forecast, updated)

    def test_uses_stale_forecast_during_provider_failure(self):
        cache = InMemoryWeatherCache()
        cache.put(
            self.location,
            CachedForecast(self.forecast, self.now - timedelta(hours=6)),
        )
        upstream = FakeProvider(error=WeatherProviderError("down"))
        provider = CachingWeatherProvider(
            upstream, cache, FixedClock(self.now)
        )

        value = provider.daily_forecast(self.location, self.forecast.date)

        self.assertEqual(value, self.forecast)

    def test_rejects_forecast_past_stale_window(self):
        cache = InMemoryWeatherCache()
        cache.put(
            self.location,
            CachedForecast(self.forecast, self.now - timedelta(hours=25)),
        )
        upstream = FakeProvider(error=WeatherProviderError("down"))
        provider = CachingWeatherProvider(
            upstream, cache, FixedClock(self.now)
        )

        with self.assertRaises(WeatherProviderError):
            provider.daily_forecast(self.location, self.forecast.date)

    def test_emits_cache_and_provider_metrics(self):
        cache = InMemoryWeatherCache()
        upstream = FakeProvider(self.forecast)
        provider = CachingWeatherProvider(
            upstream, cache, FixedClock(self.now)
        )

        with self.assertLogs("greetings_bot.weather_cache", level="INFO") as logs:
            provider.daily_forecast(self.location, self.forecast.date)
            provider.daily_forecast(self.location, self.forecast.date)

        self.assertTrue(any('"CacheMiss":1' in line for line in logs.output))
        self.assertTrue(any('"ProviderCall":1' in line for line in logs.output))
        self.assertTrue(any('"CacheHit":1' in line for line in logs.output))

    def test_emits_stale_fallback_metric(self):
        cache = InMemoryWeatherCache()
        cache.put(
            self.location,
            CachedForecast(self.forecast, self.now - timedelta(hours=6)),
        )
        provider = CachingWeatherProvider(
            FakeProvider(error=WeatherProviderError("down")),
            cache,
            FixedClock(self.now),
        )

        with self.assertLogs("greetings_bot.weather_cache", level="INFO") as logs:
            provider.daily_forecast(self.location, self.forecast.date)

        self.assertTrue(any('"ProviderError":1' in line for line in logs.output))
        self.assertTrue(any('"StaleFallback":1' in line for line in logs.output))

    def test_counts_uncached_provider_attempts_only(self):
        meter = UsageMeter()
        provider = CachingWeatherProvider(
            FakeProvider(self.forecast),
            InMemoryWeatherCache(),
            FixedClock(self.now),
            usage_meter=meter,
        )

        provider.daily_forecast(self.location, self.forecast.date)
        provider.daily_forecast(self.location, self.forecast.date)

        self.assertEqual(meter.count("weather_calls"), 1)


if __name__ == "__main__":
    unittest.main()
