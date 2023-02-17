import unittest
from datetime import datetime, timezone

from greetings_bot.notes import Note, create_note, format_note_list


class NoteTest(unittest.TestCase):
    def test_keeps_note_details(self):
        created_at = datetime(2023, 2, 3, 18, 30, tzinfo=timezone.utc)

        note = Note("a1b2c3d4", 42, "Call the dentist", created_at)

        self.assertEqual(note.id, "a1b2c3d4")
        self.assertEqual(note.owner_id, 42)
        self.assertEqual(note.text, "Call the dentist")
        self.assertEqual(note.created_at, created_at)

    def test_creates_trimmed_note(self):
        note = create_note(42, "  Call the dentist  ")

        self.assertEqual(note.owner_id, 42)
        self.assertEqual(note.text, "Call the dentist")
        self.assertEqual(len(note.id), 8)
        self.assertIsNotNone(note.created_at.tzinfo)

    def test_rejects_blank_note(self):
        with self.assertRaisesRegex(ValueError, "required"):
            create_note(42, "  ")

    def test_rejects_long_note(self):
        with self.assertRaisesRegex(ValueError, "too long"):
            create_note(42, "x" * 501)

    def test_formats_note_list(self):
        note = Note("a1b2c3d4", 42, "Call the dentist", datetime.now(timezone.utc))

        self.assertEqual(format_note_list([note]), "a1b2c3d4: Call the dentist")

    def test_shortens_long_text_in_list(self):
        note = Note("a1b2c3d4", 42, "x" * 80, datetime.now(timezone.utc))

        self.assertEqual(format_note_list([note]), "a1b2c3d4: " + "x" * 60)


if __name__ == "__main__":
    unittest.main()
