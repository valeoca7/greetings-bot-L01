import json
import tempfile
import unittest
from pathlib import Path

from greetings_bot.user_store import FileUserRepository, UserStoreError
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
            self.assertFalse((Path(str(path) + ".tmp")).exists())

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
            self.assertEqual(
                [user.telegram_id for user in restored.all()],
                [42, 77],
            )

    def test_writes_users_in_id_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            repository = FileUserRepository(path)
            repository.save(
                User(telegram_id=77, chat_id=77, first_name="Lee")
            )
            repository.save(
                User(telegram_id=42, chat_id=42, first_name="Mira")
            )

            values = json.loads(path.read_text())

            self.assertEqual([item["telegram_id"] for item in values], [42, 77])

    def test_reports_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            path.write_text("not json")

            with self.assertRaisesRegex(UserStoreError, "invalid user store"):
                FileUserRepository(path)

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "users.json"
            repository = FileUserRepository(path)

            repository.save(User(telegram_id=42, chat_id=42, first_name="Mira"))

            self.assertTrue(path.exists())

    def test_deletes_and_rewrites_a_user(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            repository = FileUserRepository(path)
            repository.save(User(42, 42, "Mira"))
            repository.save(User(77, 77, "Lee"))

            self.assertTrue(repository.delete(42))
            self.assertFalse(repository.delete(42))

            stored = json.loads(path.read_text())
            self.assertEqual([item["telegram_id"] for item in stored], [77])


if __name__ == "__main__":
    unittest.main()
