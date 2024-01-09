import unittest

from greetings_bot.users import (
    InMemoryUserRepository,
    User,
    normalize_first_name,
    normalize_locale,
    user_from_dict,
    user_to_dict,
)


class UserTest(unittest.TestCase):
    def test_keeps_telegram_profile(self):
        user = User(telegram_id=42, chat_id=84, first_name="Mira")

        self.assertEqual(user.telegram_id, 42)
        self.assertEqual(user.chat_id, 84)
        self.assertEqual(user.first_name, "Mira")
        self.assertEqual(user.locale, "en")
        self.assertEqual(user.greeting_time, "09:00")
        self.assertTrue(user.enabled)
        self.assertEqual(user.timezone, "UTC")
        self.assertIsNone(user.quiet_start)
        self.assertIsNone(user.quiet_end)
        self.assertEqual(
            user.greeting_days,
            ("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
        )
        self.assertEqual(user.digest_mode, "off")

    def test_normalizes_first_name(self):
        self.assertEqual(normalize_first_name("  Mira "), "Mira")

    def test_uses_fallback_for_a_blank_name(self):
        self.assertEqual(normalize_first_name("  "), "friend")

    def test_normalizes_locale(self):
        self.assertEqual(normalize_locale("pt-BR"), "pt")
        self.assertEqual(normalize_locale("UK"), "uk")

    def test_defaults_missing_locale(self):
        self.assertEqual(normalize_locale(None), "en")

    def test_converts_user_to_dict(self):
        user = User(telegram_id=42, chat_id=84, first_name="Mira")

        data = user_to_dict(user)

        self.assertEqual(data["telegram_id"], 42)
        self.assertEqual(data["first_name"], "Mira")
        self.assertEqual(data["greeting_time"], "09:00")
        self.assertEqual(data["timezone"], "UTC")
        self.assertIsNone(data["quiet_start"])
        self.assertEqual(
            data["greeting_days"],
            ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        )
        self.assertEqual(data["digest_mode"], "off")

    def test_defaults_timezone_in_old_records(self):
        user = user_from_dict({"telegram_id": 1, "chat_id": 1, "first_name": "Jo"})

        self.assertEqual("UTC", user.timezone)

    def test_restores_user_from_dict(self):
        original = User(telegram_id=42, chat_id=84, first_name="Mira")

        restored = user_from_dict(user_to_dict(original))

        self.assertEqual(restored, original)


class InMemoryUserRepositoryTest(unittest.TestCase):
    def test_saves_a_user(self):
        repository = InMemoryUserRepository()
        user = User(telegram_id=42, chat_id=84, first_name="Mira")

        repository.save(user)

        self.assertEqual(repository.get(42), user)
        self.assertEqual(repository.count(), 1)

    def test_returns_none_for_an_unknown_user(self):
        repository = InMemoryUserRepository()

        self.assertIsNone(repository.get(99))

    def test_lists_users_in_id_order(self):
        repository = InMemoryUserRepository()
        repository.save(User(telegram_id=77, chat_id=77, first_name="Lee"))
        repository.save(User(telegram_id=42, chat_id=42, first_name="Mira"))

        users = repository.all()

        self.assertEqual([user.telegram_id for user in users], [42, 77])


if __name__ == "__main__":
    unittest.main()
