import json
from dataclasses import dataclass
from typing import Mapping, Optional, Protocol


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


class QueueClient(Protocol):
    def send_message(self, **kwargs: object) -> Mapping[str, object]:
        ...

    def get_queue_attributes(self, **kwargs: object) -> Mapping[str, object]:
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
    def __init__(self, client: QueueClient, queue_url: str) -> None:
        self.client = client
        self.queue_url = queue_url

    def enqueue(self, message: DeliveryMessage) -> None:
        self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=message_to_body(message),
        )

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


def queue_from_env(
    environ: Mapping[str, str], client: Optional[QueueClient] = None
) -> Optional[DeliveryQueue]:
    queue_url = environ.get("DELIVERY_QUEUE_URL")
    if not queue_url:
        return None
    if client is None:
        import boto3

        client = boto3.client("sqs")
    return SqsDeliveryQueue(client, queue_url)
