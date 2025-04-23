from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Protocol


class DeliveryAdminError(RuntimeError):
    pass


@dataclass(frozen=True)
class DeliveryQueueSummary:
    pending: int
    in_flight: int
    failed: int

    def __post_init__(self) -> None:
        if min(self.pending, self.in_flight, self.failed) < 0:
            raise ValueError("delivery queue counts must not be negative")

    def to_dict(self) -> Dict[str, int]:
        return {
            "pending": self.pending,
            "in_flight": self.in_flight,
            "failed": self.failed,
        }


class DeliveryAdminOperations(Protocol):
    def summary(self) -> DeliveryQueueSummary:
        ...

    def start_redrive(self, max_rate: int) -> str:
        ...


class SqsAdminClient(Protocol):
    def get_queue_attributes(self, **request) -> Mapping[str, object]:
        ...

    def start_message_move_task(self, **request) -> Mapping[str, object]:
        ...


class SqsDeliveryAdmin:
    def __init__(
        self,
        client: SqsAdminClient,
        queue_url: str,
        dead_letter_url: str,
        queue_arn: str,
        dead_letter_arn: str,
    ) -> None:
        self.client = client
        self.queue_url = queue_url
        self.dead_letter_url = dead_letter_url
        self.queue_arn = queue_arn
        self.dead_letter_arn = dead_letter_arn

    def summary(self) -> DeliveryQueueSummary:
        try:
            main = self.client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=[
                    "ApproximateNumberOfMessages",
                    "ApproximateNumberOfMessagesNotVisible",
                ],
            )["Attributes"]
            dead_letters = self.client.get_queue_attributes(
                QueueUrl=self.dead_letter_url,
                AttributeNames=["ApproximateNumberOfMessages"],
            )["Attributes"]
            return DeliveryQueueSummary(
                int(main["ApproximateNumberOfMessages"]),
                int(main["ApproximateNumberOfMessagesNotVisible"]),
                int(dead_letters["ApproximateNumberOfMessages"]),
            )
        except Exception as error:
            raise DeliveryAdminError("delivery queue unavailable") from error

    def start_redrive(self, max_rate: int) -> str:
        if not 1 <= max_rate <= 500:
            raise ValueError("redrive rate must be between 1 and 500")
        try:
            response = self.client.start_message_move_task(
                SourceArn=self.dead_letter_arn,
                DestinationArn=self.queue_arn,
                MaxNumberOfMessagesPerSecond=max_rate,
            )
            task_handle = response["TaskHandle"]
            if not isinstance(task_handle, str) or not task_handle:
                raise ValueError("redrive task handle is missing")
            return task_handle
        except Exception as error:
            raise DeliveryAdminError("delivery redrive unavailable") from error


def delivery_admin_from_env(
    environ: Mapping[str, str],
    client: Optional[SqsAdminClient] = None,
) -> Optional[SqsDeliveryAdmin]:
    names = (
        "DELIVERY_QUEUE_URL",
        "DELIVERY_DLQ_URL",
        "DELIVERY_QUEUE_ARN",
        "DELIVERY_DLQ_ARN",
    )
    values = tuple(environ.get(name, "").strip() for name in names)
    if not any(values):
        return None
    if not all(values):
        raise ValueError("delivery admin queue configuration is incomplete")
    if client is None:
        import boto3

        client = boto3.client("sqs")
    return SqsDeliveryAdmin(client, *values)
