from datetime import datetime
from typing import Dict, Mapping

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
