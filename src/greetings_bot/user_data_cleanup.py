from dataclasses import dataclass
from typing import Protocol

from greetings_bot.dynamo_users import DynamoTable
from greetings_bot.note_store import NoteRepository
from greetings_bot.reminder_store import ReminderRepository
from greetings_bot.users import UserRepository


@dataclass(frozen=True)
class CleanupBatch:
    deleted: int
    complete: bool


class UserDataCleaner(Protocol):
    def erase_batch(
        self, telegram_id: int, limit: int = 100
    ) -> CleanupBatch:
        ...


class DynamoUserDataCleaner:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def erase_batch(
        self, telegram_id: int, limit: int = 100
    ) -> CleanupBatch:
        if not 1 <= limit <= 100:
            raise ValueError("cleanup limit must be between 1 and 100")
        result = self.table.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={
                ":pk": "USER#{}".format(telegram_id)
            },
            Limit=limit + 1,
        )
        items = [
            item for item in result.get("Items", [])
            if isinstance(item, dict)
        ]
        owned = [item for item in items if item.get("sk") != "PROFILE"]
        if owned:
            selected = owned[:limit]
            for item in selected:
                self._delete(item)
            return CleanupBatch(len(selected), False)
        profiles = [item for item in items if item.get("sk") == "PROFILE"]
        for item in profiles:
            self._delete(item)
        return CleanupBatch(len(profiles), True)

    def _delete(self, item) -> None:
        self.table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})


class RepositoryUserDataCleaner:
    def __init__(
        self,
        users: UserRepository,
        notes: NoteRepository,
        reminders: ReminderRepository,
    ) -> None:
        self.users = users
        self.notes = notes
        self.reminders = reminders

    def erase_batch(
        self, telegram_id: int, limit: int = 100
    ) -> CleanupBatch:
        if not 1 <= limit <= 100:
            raise ValueError("cleanup limit must be between 1 and 100")
        deleted = self.notes.delete_all_for(telegram_id, limit)
        if deleted == limit:
            return CleanupBatch(deleted, False)
        remaining = limit - deleted
        reminder_count = self.reminders.delete_all_for(
            telegram_id, remaining
        )
        deleted += reminder_count
        if reminder_count == remaining:
            return CleanupBatch(deleted, False)
        if self.users.delete(telegram_id):
            deleted += 1
        return CleanupBatch(deleted, True)
