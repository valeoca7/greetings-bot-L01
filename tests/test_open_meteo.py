import unittest
from datetime import date

from greetings_bot.open_meteo import forecast_params, weather_condition
from greetings_bot.weather import WeatherLocation


class OpenMeteoProviderTest(unittest.TestCase):
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
