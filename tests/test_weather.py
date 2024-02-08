import unittest
from datetime import date

from greetings_bot.weather import DailyForecast, WeatherLocation


class WeatherModelTest(unittest.TestCase):
    def test_represents_a_location(self):
        location = WeatherLocation(" Vancouver ", 49.2827, -123.1207)

        self.assertEqual(location.name, "Vancouver")
        self.assertEqual(location.latitude, 49.2827)

    def test_rejects_invalid_location_coordinates(self):
        for latitude, longitude in ((91, 0), (0, 181), (-91, 0)):
            with self.subTest(latitude=latitude, longitude=longitude):
                with self.assertRaises(ValueError):
                    WeatherLocation("Somewhere", latitude, longitude)

    def test_rejects_an_empty_location_name(self):
        with self.assertRaises(ValueError):
            WeatherLocation("  ", 0, 0)

    def test_represents_a_daily_forecast(self):
        forecast = DailyForecast(
            date(2024, 2, 5), 3.5, 8.2, "rain", 70
        )

        self.assertEqual(forecast.condition, "rain")
        self.assertEqual(forecast.precipitation_percent, 70)


if __name__ == "__main__":
    unittest.main()
