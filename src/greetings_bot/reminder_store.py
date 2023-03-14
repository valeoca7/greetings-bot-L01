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

    def all_for(self, owner_id: int) -> Sequence[Reminder]:
        reminders = [
            value for (stored_owner, _), value in self._reminders.items()
            if stored_owner == owner_id
        ]
        return sorted(reminders, key=lambda value: value.due_at)

    def due_before(self, current_time: datetime, limit: int) -> Sequence[Reminder]:
        due = [
            reminder for reminder in self._reminders.values()
            if reminder.status == "pending" and reminder.due_at <= current_time
        ]
        return sorted(due, key=lambda reminder: reminder.due_at)[:limit]
