from datetime import datetime, timezone
from typing import Dict, Mapping, Optional

from greetings_bot.dynamo_users import DynamoTable
from greetings_bot.user_deletion import DeletionRequest


def deletion_request_key(telegram_id: int) -> Dict[str, object]:
    return {
        "pk": "DELETION#{}".format(telegram_id),
        "sk": "REQUEST",
    }


def deletion_request_item(request: DeletionRequest) -> Dict[str, object]:
    item = deletion_request_key(request.telegram_id)
    item.update(
        {
            "entity": "deletion_request",
            "telegram_id": request.telegram_id,
            "token_digest": request.token_digest,
            "requested_at": request.requested_at.isoformat(),
            "expires_at": int(request.expires_at.timestamp()),
            "status": request.status,
        }
    )
    if request.confirmed_at is not None:
        item["confirmed_at"] = request.confirmed_at.isoformat()
    if request.completed_at is not None:
        item["completed_at"] = request.completed_at.isoformat()
    return item


def deletion_request_from_item(
    item: Mapping[str, object]
) -> DeletionRequest:
    status = str(item["status"])
    if status not in ("requested", "confirmed", "completed"):
        raise ValueError("invalid deletion request status")
    return DeletionRequest(
        telegram_id=int(item["telegram_id"]),
        token_digest=str(item["token_digest"]),
        requested_at=datetime.fromisoformat(str(item["requested_at"])),
        expires_at=datetime.fromtimestamp(
            int(item["expires_at"]), timezone.utc
        ),
        status=status,
        confirmed_at=_optional_time(item.get("confirmed_at")),
        completed_at=_optional_time(item.get("completed_at")),
    )


def _optional_time(value: object) -> Optional[datetime]:
    return None if value is None else datetime.fromisoformat(str(value))


class DynamoDeletionRequestRepository:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def save(self, request: DeletionRequest) -> None:
        self.table.put_item(Item=deletion_request_item(request))

    def get(self, telegram_id: int) -> Optional[DeletionRequest]:
        result = self.table.get_item(Key=deletion_request_key(telegram_id))
        item = result.get("Item")
        if not isinstance(item, dict):
            return None
        if item.get("entity") != "deletion_request":
            return None
        return deletion_request_from_item(item)
