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

    def test_deletes_owned_note(self):
        notes = InMemoryNoteRepository()
        note = Note("abcd1234", 42, "Private", datetime.now(timezone.utc))
        notes.save(note)

        self.assertTrue(notes.delete(42, "abcd1234"))
        self.assertIsNone(notes.get(42, "abcd1234"))
        self.assertFalse(notes.delete(42, "abcd1234"))

    def test_cannot_delete_another_users_note(self):
        notes = InMemoryNoteRepository()
        note = Note("abcd1234", 42, "Private", datetime.now(timezone.utc))
        notes.save(note)

        self.assertFalse(notes.delete(7, "abcd1234"))
        self.assertEqual(notes.get(42, "abcd1234"), note)

    def test_deletes_a_bounded_owner_batch(self):
        notes = InMemoryNoteRepository()
        now = datetime.now(timezone.utc)
        for note in (
            Note("a", 42, "First", now),
            Note("b", 42, "Second", now),
            Note("other", 7, "Keep", now),
        ):
            notes.save(note)

        self.assertEqual(notes.delete_all_for(42, limit=1), 1)
        self.assertEqual(len(notes.all_for(42)), 1)
        self.assertEqual(notes.delete_all_for(42, limit=100), 1)
        self.assertEqual(len(notes.all_for(7)), 1)


if __name__ == "__main__":
    unittest.main()
