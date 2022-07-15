import unittest
from pathlib import Path

from greetings_bot.settings import Settings, SettingsError


class SettingsTest(unittest.TestCase):
    def test_loads_telegram_token(self):
        settings = Settings.from_env(
            {
                "TELEGRAM_BOT_TOKEN": "secret",
                "USER_STORE_PATH": "var/users.json",
            }
        )

        self.assertEqual(settings.telegram_token, "secret")
        self.assertEqual(settings.user_store_path, Path("var/users.json"))

    def test_uses_default_user_store_path(self):
        settings = Settings.from_env({"TELEGRAM_BOT_TOKEN": "secret"})

        self.assertEqual(settings.user_store_path, Path("data/users.json"))

    def test_requires_telegram_token(self):
        with self.assertRaisesRegex(SettingsError, "TELEGRAM_BOT_TOKEN"):
            Settings.from_env({})


if __name__ == "__main__":
    unittest.main()
