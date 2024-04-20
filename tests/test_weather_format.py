import unittest
from datetime import date

from greetings_bot.weather import DailyForecast, WeatherLocation
from greetings_bot.weather_format import format_daily_forecast


class WeatherFormatTest(unittest.TestCase):
    def setUp(self):
        self.location = WeatherLocation("Vancouver", 49.2, -123.1)
        self.forecast = DailyForecast(
            date(2024, 3, 22), 2.0, 10.0, "light rain", 70
        )

    def test_formats_metric_forecast(self):
        self.assertEqual(
            format_daily_forecast(self.location, self.forecast),
            "Vancouver: light rain, 2-10°C. Precipitation chance: 70%.",
        )

    def test_formats_imperial_forecast(self):
        self.assertEqual(
            format_daily_forecast(self.location, self.forecast, "imperial"),
            "Vancouver: light rain, 36-50°F. Precipitation chance: 70%.",
        )

    def test_rejects_unknown_units(self):
        with self.assertRaises(ValueError):
            format_daily_forecast(self.location, self.forecast, "kelvin")


if __name__ == "__main__":
    unittest.main()
