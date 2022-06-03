import unittest

from greetings_bot.users import (
    InMemoryUserRepository,
    User,
    normalize_first_name,
    normalize_locale,
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

    def test_normalizes_first_name(self):
        self.assertEqual(normalize_first_name("  Mira "), "Mira")

    def test_uses_fallback_for_a_blank_name(self):
        self.assertEqual(normalize_first_name("  "), "friend")

    def test_normalizes_locale(self):
        self.assertEqual(normalize_locale("pt-BR"), "pt")
        self.assertEqual(normalize_locale("UK"), "uk")

    def test_defaults_missing_locale(self):
        self.assertEqual(normalize_locale(None), "en")


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


if __name__ == "__main__":
    unittest.main()
