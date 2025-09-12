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

    def delete_all_for(self, owner_id: int, limit: int = 100) -> int:
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

    def delete(self, owner_id: int, note_id: str) -> bool:
        key = (owner_id, note_id)
        if key not in self._notes:
            return False
        del self._notes[key]
        return True

    def delete_all_for(self, owner_id: int, limit: int = 100) -> int:
        if not 1 <= limit <= 100:
            raise ValueError("note deletion limit must be between 1 and 100")
        keys = sorted(
            key for key in self._notes if key[0] == owner_id
        )[:limit]
        for key in keys:
            del self._notes[key]
        return len(keys)
