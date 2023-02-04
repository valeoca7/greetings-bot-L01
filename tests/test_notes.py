import unittest
from datetime import datetime, timezone

from greetings_bot.notes import Note


class NoteTest(unittest.TestCase):
    def test_keeps_note_details(self):
        created_at = datetime(2023, 2, 3, 18, 30, tzinfo=timezone.utc)

        note = Note("a1b2c3d4", 42, "Call the dentist", created_at)

        self.assertEqual(note.id, "a1b2c3d4")
        self.assertEqual(note.owner_id, 42)
        self.assertEqual(note.text, "Call the dentist")
        self.assertEqual(note.created_at, created_at)


if __name__ == "__main__":
    unittest.main()
