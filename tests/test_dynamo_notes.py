import unittest
from datetime import datetime, timezone

from greetings_bot.dynamo_notes import (
    DynamoNoteRepository,
    note_from_item,
    note_item,
    note_key,
)
from greetings_bot.notes import Note


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, *, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}

    def get_item(self, *, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {} if item is None else {"Item": item}

    def query(self, **kwargs):
        owner = kwargs["ExpressionAttributeValues"][":pk"]
        items = [
            item for (pk, sk), item in self.items.items()
            if pk == owner and sk.startswith("NOTE#")
        ]
        return {"Items": items}


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


class DynamoNoteRepositoryTest(unittest.TestCase):
    def test_saves_and_loads_owned_note(self):
        notes = DynamoNoteRepository(FakeTable())
        note = Note(
            "abcd1234",
            42,
            "Call the dentist",
            datetime(2023, 2, 28, 18, 0, tzinfo=timezone.utc),
        )

        notes.save(note)

        self.assertEqual(notes.get(42, "abcd1234"), note)
        self.assertIsNone(notes.get(7, "abcd1234"))

    def test_lists_only_notes_in_owner_partition(self):
        notes = DynamoNoteRepository(FakeTable())
        first = Note("aaaa1111", 42, "First", datetime(2023, 2, 27, tzinfo=timezone.utc))
        later = Note("bbbb2222", 42, "Later", datetime(2023, 2, 28, tzinfo=timezone.utc))
        other = Note("cccc3333", 7, "Other", datetime(2023, 2, 26, tzinfo=timezone.utc))
        for note in (later, first, other):
            notes.save(note)

        self.assertEqual(notes.all_for(42), [first, later])


if __name__ == "__main__":
    unittest.main()
