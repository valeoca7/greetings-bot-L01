import unittest
from datetime import date

from greetings_bot.open_meteo import (
    FORECAST_ENDPOINT,
    OpenMeteoWeatherProvider,
    forecast_params,
    weather_provider_from_env,
    weather_condition,
)
from greetings_bot.weather import WeatherLocation, WeatherProviderError


class OpenMeteoProviderTest(unittest.TestCase):
    def test_reads_timeout_from_environment(self):
        provider = weather_provider_from_env(
            {"WEATHER_TIMEOUT_SECONDS": "3"}, lambda url, timeout: None
        )

        self.assertEqual(provider.client.timeout, 3)

    def test_rejects_invalid_configured_timeout(self):
        for value in ("slow", "0"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    weather_provider_from_env({"WEATHER_TIMEOUT_SECONDS": value})

    def test_reads_a_daily_forecast(self):
        class Client:
            def get(self, endpoint, params):
                self.endpoint = endpoint
                self.params = params
                return {
                    "daily": {
                        "time": ["2024-02-20"],
                        "temperature_2m_min": [3.2],
                        "temperature_2m_max": [8.7],
                        "precipitation_probability_max": [65],
                        "weather_code": [61],
                    }
                }

        client = Client()
        provider = OpenMeteoWeatherProvider(client)
        location = WeatherLocation("Vancouver", 49.2827, -123.1207)

        forecast = provider.daily_forecast(location, date(2024, 2, 20))

        self.assertEqual(client.endpoint, FORECAST_ENDPOINT)
        self.assertEqual(forecast.low_celsius, 3.2)
        self.assertEqual(forecast.high_celsius, 8.7)
        self.assertEqual(forecast.condition, "rain")
        self.assertEqual(forecast.precipitation_percent, 65)

    def test_rejects_an_incomplete_provider_response(self):
        class Client:
            def get(self, endpoint, params):
                return {"daily": {"time": []}}

        provider = OpenMeteoWeatherProvider(Client())

        with self.assertRaisesRegex(WeatherProviderError, "provider unavailable"):
            provider.daily_forecast(
                WeatherLocation("Vancouver", 49.2, -123.1),
                date(2024, 2, 20),
            )

    def test_normalizes_transport_errors(self):
        class Client:
            def get(self, endpoint, params):
                raise OSError("timed out")

        with self.assertRaises(WeatherProviderError):
            OpenMeteoWeatherProvider(Client()).daily_forecast(
                WeatherLocation("Vancouver", 49.2, -123.1),
                date(2024, 2, 20),
            )

    def test_maps_weather_codes_to_short_conditions(self):
        expected = {
            0: "clear",
            2: "partly cloudy",
            3: "overcast",
            45: "fog",
            53: "drizzle",
            63: "rain",
            75: "snow",
            95: "thunderstorm",
            100: "unknown conditions",
        }

        for code, condition in expected.items():
            with self.subTest(code=code):
                self.assertEqual(weather_condition(code), condition)

    def test_builds_a_single_day_request(self):
        params = forecast_params(
            WeatherLocation("Vancouver", 49.2827, -123.1207),
            date(2024, 2, 14),
        )

        self.assertEqual(params["latitude"], 49.2827)
        self.assertEqual(params["longitude"], -123.1207)
        self.assertEqual(params["start_date"], "2024-02-14")
        self.assertEqual(params["end_date"], "2024-02-14")
        self.assertEqual(params["timezone"], "auto")
        self.assertIn("weather_code", params["daily"])


if __name__ == "__main__":
    unittest.main()
