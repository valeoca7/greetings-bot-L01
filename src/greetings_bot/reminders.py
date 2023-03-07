from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal


ReminderStatus = Literal["pending", "sent", "cancelled"]


@dataclass(frozen=True)
class Reminder:
    id: str
    owner_id: int
    chat_id: int
    text: str
    due_at: datetime
    created_at: datetime
    status: ReminderStatus = "pending"


def mark_sent(reminder: Reminder) -> Reminder:
    return replace(reminder, status="sent")
