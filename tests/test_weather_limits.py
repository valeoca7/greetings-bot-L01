import unittest
from datetime import date, datetime, timedelta, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.weather import DailyForecast, WeatherLocation, WeatherProviderError
from greetings_bot.weather_limits import RateLimitedWeatherProvider


class FakeProvider:
    def __init__(self):
        self.calls = 0

    def daily_forecast(self, location, forecast_date):
        self.calls += 1
        return DailyForecast(forecast_date, 4, 10, "clear", 5)


class WeatherRateLimitTest(unittest.TestCase):
    def test_limits_provider_calls_per_runtime(self):
        upstream = FakeProvider()
        provider = RateLimitedWeatherProvider(upstream, max_calls=2)
        location = WeatherLocation("Vancouver", 49.2, -123.1)

        provider.daily_forecast(location, date(2024, 6, 17))
        provider.daily_forecast(location, date(2024, 6, 18))

        with self.assertRaisesRegex(WeatherProviderError, "limit"):
            provider.daily_forecast(location, date(2024, 6, 19))
        self.assertEqual(upstream.calls, 2)

    def test_rejects_non_positive_call_limit(self):
        with self.assertRaises(ValueError):
            RateLimitedWeatherProvider(FakeProvider(), max_calls=0)

    def test_resets_limit_after_one_minute(self):
        clock = FixedClock(datetime(2024, 7, 8, 18, 0, tzinfo=timezone.utc))
        upstream = FakeProvider()
        provider = RateLimitedWeatherProvider(
            upstream, max_calls=1, clock=clock
        )
        location = WeatherLocation("Vancouver", 49.2, -123.1)
        provider.daily_forecast(location, date(2024, 7, 8))
        clock.current_time += timedelta(minutes=1)

        provider.daily_forecast(location, date(2024, 7, 9))

        self.assertEqual(upstream.calls, 2)


if __name__ == "__main__":
    unittest.main()
