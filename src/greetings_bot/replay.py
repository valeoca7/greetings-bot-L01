from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple

from greetings_bot.delivery_queue import DeliveryMessage, message_from_body


@dataclass(frozen=True)
class ReplayPlan:
    messages: Tuple[DeliveryMessage, ...]
    rejected_record_ids: Tuple[str, ...]
    duplicate_record_ids: Tuple[str, ...]


def plan_replay(event: Mapping[str, object], limit: int = 10) -> ReplayPlan:
    if not 1 <= limit <= 100:
        raise ValueError("replay limit must be between 1 and 100")
    records = event.get("Records", [])
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise ValueError("replay records must be a list")
    if len(records) > limit:
        raise ValueError("replay batch exceeds its limit")
    messages = []
    rejected = []
    duplicates = []
    delivery_ids = set()
    for raw_record in records:
        if not isinstance(raw_record, Mapping):
            rejected.append("unknown")
            continue
        record_id = str(raw_record.get("messageId", "unknown"))
        try:
            body = raw_record["body"]
            if not isinstance(body, str):
                raise ValueError("delivery body must be text")
            message = message_from_body(body)
        except (KeyError, TypeError, ValueError):
            rejected.append(record_id)
            continue
        if message.id in delivery_ids:
            duplicates.append(record_id)
            continue
        delivery_ids.add(message.id)
        messages.append(message)
    return ReplayPlan(tuple(messages), tuple(rejected), tuple(duplicates))
