import logging
import os
from typing import Dict, List, Mapping, Protocol

from greetings_bot.delivery_queue import DeliveryMessage, message_from_body
from greetings_bot.dynamo_receipts import DynamoDeliveryReceiptLedger
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.telegram_client import TelegramBotClient

logger = logging.getLogger(__name__)


class MessageSender(Protocol):
    def send(self, message: DeliveryMessage) -> None:
        ...


class DeliveryReceiptLedger(Protocol):
    def contains(self, delivery_id: str) -> bool:
        ...

    def record(self, delivery_id: str) -> None:
        ...


class InMemoryDeliveryReceiptLedger:
    def __init__(self) -> None:
        self.ids = set()

    def contains(self, delivery_id: str) -> bool:
        return delivery_id in self.ids

    def record(self, delivery_id: str) -> None:
        self.ids.add(delivery_id)


class DeliveryQueueWorker:
    def __init__(
        self, sender: MessageSender, receipts: DeliveryReceiptLedger
    ) -> None:
        self.sender = sender
        self.receipts = receipts

    def handle(self, event: Mapping[str, object]) -> Dict[str, List[Dict[str, str]]]:
        failures = []
        for record in event.get("Records", []):
            message_id = str(record.get("messageId", "unknown"))
            try:
                message = message_from_body(str(record["body"]))
                if self.receipts.contains(message.id):
                    continue
                self.sender.send(message)
                self.receipts.record(message.id)
            except (KeyError, TypeError, ValueError, RuntimeError, OSError):
                # TODO: include the delivery correlation ID in retry logs.
                logger.warning("delivery failed; queue record will be retried")
                failures.append({"itemIdentifier": message_id})
        return {"batchItemFailures": failures}


def build_default_worker(
    environ: Mapping[str, str] = os.environ,
    dynamodb_resource: DynamoResource = None,
    sender: MessageSender = None,
) -> DeliveryQueueWorker:
    table_name = environ.get("USER_TABLE_NAME")
    token = environ.get("TELEGRAM_BOT_TOKEN")
    if not table_name or (not token and sender is None):
        raise ValueError("worker configuration is incomplete")
    users = repository_for_table(table_name, dynamodb_resource)
    receipts = DynamoDeliveryReceiptLedger(users.table)
    return DeliveryQueueWorker(sender or TelegramBotClient(token), receipts)


_worker = None


def handle_event(event: Mapping[str, object], context: object = None):
    global _worker
    if _worker is None:
        _worker = build_default_worker()
    return _worker.handle(event)
