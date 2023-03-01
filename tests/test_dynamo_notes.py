import unittest
from datetime import datetime, timezone

from greetings_bot.dynamo_notes import note_from_item, note_item, note_key
from greetings_bot.notes import Note


class NoteMappingTest(unittest.TestCase):
    def test_builds_owned_note_key(self):
        self.assertEqual(
            note_key(42, "abcd1234"),
            {"pk": "USER#42", "sk": "NOTE#abcd1234"},
        )

    def test_round_trips_note_item(self):
        note = Note(
            "abcd1234",
            42,
            "Call the dentist",
            datetime(2023, 2, 28, 18, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(note_from_item(note_item(note)), note)


if __name__ == "__main__":
    unittest.main()
