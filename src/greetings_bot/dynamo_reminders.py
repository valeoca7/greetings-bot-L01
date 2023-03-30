from datetime import datetime
from typing import Dict, Mapping

from greetings_bot.reminders import Reminder


def reminder_key(owner_id: int, reminder_id: str) -> Dict[str, object]:
    return {
        "pk": "USER#{}".format(owner_id),
        "sk": "REMINDER#{}".format(reminder_id),
    }


def reminder_item(reminder: Reminder) -> Dict[str, object]:
    item = reminder_key(reminder.owner_id, reminder.id)
    item.update(
        {
            "entity": "reminder",
            "reminder_id": reminder.id,
            "owner_id": reminder.owner_id,
            "chat_id": reminder.chat_id,
            "text": reminder.text,
            "due_at": reminder.due_at.isoformat(),
            "created_at": reminder.created_at.isoformat(),
            "status": reminder.status,
        }
    )
    if reminder.status == "pending":
        item["gsi1pk"] = "REMINDER#PENDING"
        item["gsi1sk"] = "{}#{}#{}".format(
            reminder.due_at.isoformat(), reminder.owner_id, reminder.id
        )
    return item


def reminder_from_item(item: Mapping[str, object]) -> Reminder:
    return Reminder(
        id=str(item["reminder_id"]),
        owner_id=int(item["owner_id"]),
        chat_id=int(item["chat_id"]),
        text=str(item["text"]),
        due_at=datetime.fromisoformat(str(item["due_at"])),
        created_at=datetime.fromisoformat(str(item["created_at"])),
        status=str(item.get("status", "pending")),
    )
