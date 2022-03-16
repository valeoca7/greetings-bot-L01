import unittest

from greetings_bot.users import InMemoryUserRepository, User


class UserTest(unittest.TestCase):
    def test_keeps_telegram_profile(self):
        user = User(telegram_id=42, chat_id=84, first_name="Mira")

        self.assertEqual(user.telegram_id, 42)
        self.assertEqual(user.chat_id, 84)
        self.assertEqual(user.first_name, "Mira")


class InMemoryUserRepositoryTest(unittest.TestCase):
    def test_saves_a_user(self):
        repository = InMemoryUserRepository()
        user = User(telegram_id=42, chat_id=84, first_name="Mira")

        repository.save(user)

        self.assertEqual(repository.get(42), user)

    def test_returns_none_for_an_unknown_user(self):
        repository = InMemoryUserRepository()

        self.assertIsNone(repository.get(99))


if __name__ == "__main__":
    unittest.main()
