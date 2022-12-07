import unittest
from pathlib import Path

from greetings_bot.settings import Settings, SettingsError


class SettingsTest(unittest.TestCase):
    def test_loads_telegram_token(self):
        settings = Settings.from_env(
            {
                "TELEGRAM_BOT_TOKEN": "secret",
                "USER_STORE_PATH": "var/users.json",
                "USER_TABLE_NAME": "greetings-users",
            }
        )

        self.assertEqual(settings.telegram_token, "secret")
        self.assertEqual(settings.user_store_path, Path("var/users.json"))
        self.assertEqual(settings.user_table_name, "greetings-users")

    def test_uses_default_user_store_path(self):
        settings = Settings.from_env({"TELEGRAM_BOT_TOKEN": "secret"})

        self.assertEqual(settings.user_store_path, Path("data/users.json"))
        self.assertIsNone(settings.user_table_name)

    def test_requires_telegram_token(self):
        with self.assertRaisesRegex(SettingsError, "TELEGRAM_BOT_TOKEN"):
            Settings.from_env({})


if __name__ == "__main__":
    unittest.main()
