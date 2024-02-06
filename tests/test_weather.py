import unittest
from datetime import date

from greetings_bot.weather import DailyForecast, WeatherLocation


class WeatherModelTest(unittest.TestCase):
    def test_represents_a_location(self):
        location = WeatherLocation("Vancouver", 49.2827, -123.1207)

        self.assertEqual(location.name, "Vancouver")
        self.assertEqual(location.latitude, 49.2827)

    def test_represents_a_daily_forecast(self):
        forecast = DailyForecast(
            date(2024, 2, 5), 3.5, 8.2, "rain", 70
        )

        self.assertEqual(forecast.condition, "rain")
        self.assertEqual(forecast.precipitation_percent, 70)


if __name__ == "__main__":
    unittest.main()
