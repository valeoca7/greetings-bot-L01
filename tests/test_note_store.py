import unittest
from datetime import datetime, timezone

from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.notes import Note


class InMemoryNoteRepositoryTest(unittest.TestCase):
    def test_saves_note(self):
        notes = InMemoryNoteRepository()
        note = Note("abcd1234", 42, "Call the dentist", datetime.now(timezone.utc))

        notes.save(note)

        self.assertEqual(notes.get(42, "abcd1234"), note)

    def test_does_not_return_another_users_note(self):
        notes = InMemoryNoteRepository()
        note = Note("abcd1234", 42, "Private", datetime.now(timezone.utc))
        notes.save(note)

        self.assertIsNone(notes.get(7, "abcd1234"))


if __name__ == "__main__":
    unittest.main()
