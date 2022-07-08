import json
import tempfile
import unittest
from pathlib import Path

from greetings_bot.user_store import FileUserRepository
from greetings_bot.users import User


class FileUserRepositoryTest(unittest.TestCase):
    def test_starts_empty_when_file_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"

            repository = FileUserRepository(path)

            self.assertEqual(repository.count(), 0)
            self.assertIsNone(repository.get(42))

    def test_writes_user_to_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            repository = FileUserRepository(path)

            repository.save(User(telegram_id=42, chat_id=42, first_name="Mira"))

            values = json.loads(path.read_text())
            self.assertEqual(values[0]["telegram_id"], 42)
            self.assertEqual(values[0]["first_name"], "Mira")

    def test_loads_saved_user(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            FileUserRepository(path).save(
                User(telegram_id=42, chat_id=42, first_name="Mira")
            )

            repository = FileUserRepository(path)

            self.assertEqual(repository.get(42).first_name, "Mira")

    def test_preserves_multiple_users(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            repository = FileUserRepository(path)
            repository.save(
                User(telegram_id=42, chat_id=42, first_name="Mira")
            )
            repository.save(
                User(telegram_id=77, chat_id=77, first_name="Lee")
            )

            restored = FileUserRepository(path)

            self.assertEqual(restored.count(), 2)
            self.assertEqual(restored.get(42).first_name, "Mira")
            self.assertEqual(restored.get(77).first_name, "Lee")


if __name__ == "__main__":
    unittest.main()
