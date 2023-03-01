from datetime import datetime
from typing import Dict, Mapping, Optional

from greetings_bot.dynamo_users import DynamoTable
from greetings_bot.notes import Note


def note_key(owner_id: int, note_id: str) -> Dict[str, object]:
    return {
        "pk": "USER#{}".format(owner_id),
        "sk": "NOTE#{}".format(note_id),
    }


def note_item(note: Note) -> Dict[str, object]:
    item = note_key(note.owner_id, note.id)
    item.update(
        {
            "entity": "note",
            "note_id": note.id,
            "owner_id": note.owner_id,
            "text": note.text,
            "created_at": note.created_at.isoformat(),
        }
    )
    return item


def note_from_item(item: Mapping[str, object]) -> Note:
    return Note(
        id=str(item["note_id"]),
        owner_id=int(item["owner_id"]),
        text=str(item["text"]),
        created_at=datetime.fromisoformat(str(item["created_at"])),
    )


class DynamoNoteRepository:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def save(self, note: Note) -> None:
        self.table.put_item(Item=note_item(note))

    def get(self, owner_id: int, note_id: str) -> Optional[Note]:
        result = self.table.get_item(Key=note_key(owner_id, note_id))
        item = result.get("Item")
        if not isinstance(item, dict) or item.get("entity") != "note":
            return None
        return note_from_item(item)
