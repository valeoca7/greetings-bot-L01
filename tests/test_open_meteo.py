import unittest
from datetime import date

from greetings_bot.open_meteo import forecast_params
from greetings_bot.weather import WeatherLocation


class OpenMeteoProviderTest(unittest.TestCase):
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
