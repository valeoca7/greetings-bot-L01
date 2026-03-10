import json
from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Protocol

from greetings_bot.clock import Clock, SystemClock
from greetings_bot.usage import UsageMeter


@dataclass(frozen=True)
class DeliveryMessage:
    id: str
    chat_id: int
    text: str
    kind: str


class DeliveryQueue(Protocol):
    def enqueue(self, message: DeliveryMessage) -> None:
        ...

    def depth(self) -> int:
        ...

    def enqueue_many(self, messages: Iterable[DeliveryMessage]) -> None:
        ...


class QueueClient(Protocol):
    def send_message(self, **kwargs: object) -> Mapping[str, object]:
        ...

    def get_queue_attributes(self, **kwargs: object) -> Mapping[str, object]:
        ...

    def send_message_batch(self, **kwargs: object) -> Mapping[str, object]:
        ...


def message_to_body(message: DeliveryMessage) -> str:
    return json.dumps(
        {
            "id": message.id,
            "chat_id": message.chat_id,
            "text": message.text,
            "kind": message.kind,
        },
        separators=(",", ":"),
    )


def message_from_body(body: str) -> DeliveryMessage:
    value = json.loads(body)
    if not isinstance(value, dict):
        raise ValueError("delivery message must be an object")
    return DeliveryMessage(
        id=str(value["id"]),
        chat_id=int(value["chat_id"]),
        text=str(value["text"]),
        kind=str(value["kind"]),
    )


class SqsDeliveryQueue:
    def __init__(
        self,
        client: QueueClient,
        queue_url: str,
        usage_meter: Optional[UsageMeter] = None,
        clock: Optional[Clock] = None,
    ) -> None:
        self.client = client
        self.queue_url = queue_url
        self.usage_meter = usage_meter
        self.clock = clock or SystemClock()

    def enqueue(self, message: DeliveryMessage) -> None:
        self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=message_to_body(message),
        )
        self._record_usage(1)

    def depth(self) -> int:
        response = self.client.get_queue_attributes(
            QueueUrl=self.queue_url,
            AttributeNames=[
                "ApproximateNumberOfMessages",
                "ApproximateNumberOfMessagesNotVisible",
                "ApproximateNumberOfMessagesDelayed",
            ],
        )
        attributes = response.get("Attributes", {})
        if not isinstance(attributes, Mapping):
            raise ValueError("invalid queue attributes")
        return sum(
            int(attributes.get(name, "0"))
            for name in (
                "ApproximateNumberOfMessages",
                "ApproximateNumberOfMessagesNotVisible",
                "ApproximateNumberOfMessagesDelayed",
            )
        )

    def enqueue_many(self, messages: Iterable[DeliveryMessage]) -> None:
        batch = []
        for message in messages:
            batch.append(
                {
                    "Id": str(len(batch)),
                    "MessageBody": message_to_body(message),
                }
            )
            if len(batch) == 10:
                self._send_batch(batch)
                batch = []
        if batch:
            self._send_batch(batch)

    def _send_batch(self, entries: list) -> None:
        response = self.client.send_message_batch(
            QueueUrl=self.queue_url,
            Entries=entries,
        )
        failed = response.get("Failed", [])
        self._record_usage(len(entries) - len(failed))
        if failed:
            raise RuntimeError("delivery queue rejected a message batch")

    def _record_usage(self, amount: int) -> None:
        if self.usage_meter is not None and amount:
            self.usage_meter.record(
                "queued_messages", amount, self.clock.now().date()
            )


def queue_from_env(
    environ: Mapping[str, str],
    client: Optional[QueueClient] = None,
    usage_meter: Optional[UsageMeter] = None,
    clock: Optional[Clock] = None,
) -> Optional[DeliveryQueue]:
    queue_url = environ.get("DELIVERY_QUEUE_URL")
    if not queue_url:
        return None
    if client is None:
        import boto3

        client = boto3.client("sqs")
    return SqsDeliveryQueue(client, queue_url, usage_meter, clock)
