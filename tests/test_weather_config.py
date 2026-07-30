import unittest

from greetings_bot.weather_config import WeatherSettings, weather_settings_from_env


class WeatherSettingsTest(unittest.TestCase):
    def test_uses_runtime_defaults(self):
        self.assertEqual(weather_settings_from_env({}), WeatherSettings())

    def test_reads_all_weather_limits(self):
        settings = weather_settings_from_env(
            {
                "WEATHER_TIMEOUT_SECONDS": "4",
                "WEATHER_MAX_CALLS": "12",
                "WEATHER_CACHE_MINUTES": "45",
                "WEATHER_STALE_HOURS": "18",
            }
        )

        self.assertEqual(settings, WeatherSettings(4, 12, 45, 18))

    def test_names_the_invalid_weather_setting(self):
        for name in (
            "WEATHER_TIMEOUT_SECONDS",
            "WEATHER_MAX_CALLS",
            "WEATHER_CACHE_MINUTES",
            "WEATHER_STALE_HOURS",
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, name):
                    weather_settings_from_env({name: "0"})


if __name__ == "__main__":
    unittest.main()
