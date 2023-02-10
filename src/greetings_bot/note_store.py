from typing import Dict, Optional, Protocol, Sequence, Tuple

from greetings_bot.notes import Note


class NoteRepository(Protocol):
    def save(self, note: Note) -> None:
        ...

    def get(self, owner_id: int, note_id: str) -> Optional[Note]:
        ...

    def all_for(self, owner_id: int) -> Sequence[Note]:
        ...

    def delete(self, owner_id: int, note_id: str) -> bool:
        ...


class InMemoryNoteRepository:
    def __init__(self) -> None:
        self._notes: Dict[Tuple[int, str], Note] = {}

    def save(self, note: Note) -> None:
        self._notes[(note.owner_id, note.id)] = note

    def get(self, owner_id: int, note_id: str) -> Optional[Note]:
        return self._notes.get((owner_id, note_id))

    def all_for(self, owner_id: int) -> Sequence[Note]:
        notes = [
            note for (stored_owner, _), note in self._notes.items()
            if stored_owner == owner_id
        ]
        return sorted(notes, key=lambda note: note.created_at)
