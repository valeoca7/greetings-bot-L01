from datetime import datetime
from typing import Dict, Mapping, Optional, Sequence

from greetings_bot.dynamo_users import DynamoTable
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


class DynamoReminderRepository:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def save(self, reminder: Reminder) -> None:
        self.table.put_item(Item=reminder_item(reminder))

    def get(self, owner_id: int, reminder_id: str) -> Optional[Reminder]:
        result = self.table.get_item(Key=reminder_key(owner_id, reminder_id))
        item = result.get("Item")
        if not isinstance(item, dict) or item.get("entity") != "reminder":
            return None
        return reminder_from_item(item)

    def all_for(self, owner_id: int) -> Sequence[Reminder]:
        result = self.table.query(
            KeyConditionExpression="pk = :pk AND begins_with(sk, :prefix)",
            ExpressionAttributeValues={
                ":pk": "USER#{}".format(owner_id),
                ":prefix": "REMINDER#",
            },
        )
        reminders = [
            reminder_from_item(item)
            for item in result.get("Items", [])
            if isinstance(item, dict) and item.get("entity") == "reminder"
        ]
        return sorted(reminders, key=lambda reminder: reminder.due_at)
