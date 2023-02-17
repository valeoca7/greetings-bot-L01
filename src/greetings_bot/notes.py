from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4
from typing import Iterable


@dataclass(frozen=True)
class Note:
    id: str
    owner_id: int
    text: str
    created_at: datetime


def create_note(owner_id: int, text: str) -> Note:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("note text is required")
    if len(clean_text) > 500:
        raise ValueError("note text is too long")
    return Note(
        id=uuid4().hex[:8],
        owner_id=owner_id,
        text=clean_text,
        created_at=datetime.now(timezone.utc),
    )


def format_note_list(notes: Iterable[Note]) -> str:
    return "\n".join(
        "{}: {}".format(note.id, note.text[:60]) for note in notes
    )
