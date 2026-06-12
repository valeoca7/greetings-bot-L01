import unittest
from datetime import date, datetime, timezone

from greetings_bot.telegram import Reply
from greetings_bot.users import User
from greetings_bot.weather import DailyForecast, WeatherLocation, WeatherProviderError
from greetings_bot.weather_summary import add_weather_summaries


class FakeProvider:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def daily_forecast(self, location, forecast_date):
        self.calls.append((location, forecast_date))
        if self.error:
            raise self.error
        return DailyForecast(forecast_date, 4, 11, "cloudy", 30)


class WeatherSummaryTest(unittest.TestCase):
    def test_appends_opted_in_weather_to_a_greeting(self):
        location = WeatherLocation("Vancouver", 49.2, -123.1)
        user = User(
            42,
            84,
            "Mira",
            timezone="America/Vancouver",
            weather_location=location,
            weather_summary=True,
            digest_mode="daily",
        )
        provider = FakeProvider()
        current = datetime(2024, 5, 8, 2, 0, tzinfo=timezone.utc)

        replies = add_weather_summaries(
            [Reply(84, "Good evening, Mira!")], [user], current, provider
        )

        self.assertEqual(provider.calls, [(location, date(2024, 5, 7))])
        self.assertEqual(
            replies[0].text,
            "Good evening, Mira!\n\n"
            "Vancouver: cloudy, 4-11°C. Precipitation chance: 30%.",
        )

    def test_skips_users_without_a_subscription(self):
        user = User(42, 84, "Mira")
        provider = FakeProvider()

        replies = add_weather_summaries(
            [Reply(84, "Good day, Mira!")],
            [user],
            datetime(2024, 5, 8, tzinfo=timezone.utc),
            provider,
        )

        self.assertEqual(replies, [Reply(84, "Good day, Mira!")])
        self.assertEqual(provider.calls, [])

    def test_keeps_greeting_when_provider_fails(self):
        user = User(
            42,
            84,
            "Mira",
            weather_location=WeatherLocation("Vancouver", 49.2, -123.1),
            weather_summary=True,
            digest_mode="daily",
        )
        provider = FakeProvider(WeatherProviderError("down"))

        with self.assertLogs("greetings_bot.weather_summary", level="WARNING") as logs:
            replies = add_weather_summaries(
                [Reply(84, "Good day, Mira!")],
                [user],
                datetime(2024, 5, 8, tzinfo=timezone.utc),
                provider,
            )

        self.assertEqual(replies, [Reply(84, "Good day, Mira!")])
        self.assertIn('"event":"weather_summary_failed"', logs.output[0])
        self.assertIn('"user_id":42', logs.output[0])

    def test_pauses_weather_when_daily_digest_is_off(self):
        user = User(
            42,
            84,
            "Mira",
            weather_location=WeatherLocation("Vancouver", 49.2, -123.1),
            weather_summary=True,
            digest_mode="off",
        )
        provider = FakeProvider()

        replies = add_weather_summaries(
            [Reply(84, "Good day, Mira!")],
            [user],
            datetime(2024, 5, 8, tzinfo=timezone.utc),
            provider,
        )

        self.assertEqual(replies, [Reply(84, "Good day, Mira!")])
        self.assertEqual(provider.calls, [])

    def test_accepts_a_request_local_time_from_dispatch(self):
        location = WeatherLocation("Tokyo", 35.7, 139.7)
        user = User(
            42,
            84,
            "Mira",
            timezone="Asia/Tokyo",
            weather_location=location,
            weather_summary=True,
            digest_mode="daily",
        )
        provider = FakeProvider()
        selected_local_time = datetime(2024, 5, 9, 3, 0, tzinfo=timezone.utc)

        add_weather_summaries(
            [Reply(84, "Hello")],
            [user],
            datetime(2024, 5, 8, 18, 0, tzinfo=timezone.utc),
            provider,
            {42: selected_local_time},
        )

        self.assertEqual(provider.calls[0][1], date(2024, 5, 9))


if __name__ == "__main__":
    unittest.main()
