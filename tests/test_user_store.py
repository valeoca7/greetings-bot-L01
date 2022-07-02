import json
import tempfile
import unittest
from pathlib import Path

from greetings_bot.user_store import FileUserRepository
from greetings_bot.users import User


class FileUserRepositoryTest(unittest.TestCase):
    def test_writes_user_to_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "users.json"
            repository = FileUserRepository(path)

            repository.save(User(telegram_id=42, chat_id=42, first_name="Mira"))

            values = json.loads(path.read_text())
            self.assertEqual(values[0]["telegram_id"], 42)
            self.assertEqual(values[0]["first_name"], "Mira")


if __name__ == "__main__":
    unittest.main()
