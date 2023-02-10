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

    def test_lists_only_owner_notes_in_creation_order(self):
        notes = InMemoryNoteRepository()
        later = Note("bbbb2222", 42, "Second", datetime(2023, 2, 9, tzinfo=timezone.utc))
        first = Note("aaaa1111", 42, "First", datetime(2023, 2, 8, tzinfo=timezone.utc))
        other = Note("cccc3333", 7, "Other", datetime(2023, 2, 7, tzinfo=timezone.utc))
        for note in (later, first, other):
            notes.save(note)

        self.assertEqual(notes.all_for(42), [first, later])


if __name__ == "__main__":
    unittest.main()
