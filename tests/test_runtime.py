import unittest

from greetings_bot.runtime import process_payload
from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.users import InMemoryUserRepository


class RuntimeTest(unittest.TestCase):
    def test_processes_an_update_payload(self):
        payload = {
            "update_id": 1001,
            "message": {
                "message_id": 7,
                "from": {"id": 42, "first_name": "Mira"},
                "chat": {"id": 42},
                "text": "/start",
            },
        }
        users = InMemoryUserRepository()

        reply = process_payload(payload, users)

        self.assertEqual(reply, {"chat_id": 42, "text": "Hello, Mira!"})
        self.assertIsNotNone(users.get(42))

    def test_returns_none_when_no_reply_is_needed(self):
        self.assertIsNone(process_payload({"update_id": 1002}))

    def test_keeps_notes_in_injected_repository(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        register = {
            "update_id": 1001,
            "message": {
                "message_id": 7,
                "from": {"id": 42, "first_name": "Mira"},
                "chat": {"id": 42},
                "text": "/register",
            },
        }
        process_payload(register, users, notes)
        register["message"]["text"] = "/note add Pack a book"

        process_payload(register, users, notes)

        self.assertEqual(notes.all_for(42)[0].text, "Pack a book")


if __name__ == "__main__":
    unittest.main()
