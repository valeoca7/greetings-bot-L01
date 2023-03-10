from datetime import datetime
from typing import Dict, Optional, Protocol, Sequence, Tuple

from greetings_bot.reminders import Reminder


class ReminderRepository(Protocol):
    def save(self, reminder: Reminder) -> None:
        ...

    def get(self, owner_id: int, reminder_id: str) -> Optional[Reminder]:
        ...

    def all_for(self, owner_id: int) -> Sequence[Reminder]:
        ...

    def due_before(self, current_time: datetime, limit: int) -> Sequence[Reminder]:
        ...


class InMemoryReminderRepository:
    def __init__(self) -> None:
        self._reminders: Dict[Tuple[int, str], Reminder] = {}

    def save(self, reminder: Reminder) -> None:
        self._reminders[(reminder.owner_id, reminder.id)] = reminder

    def get(self, owner_id: int, reminder_id: str) -> Optional[Reminder]:
        return self._reminders.get((owner_id, reminder_id))
