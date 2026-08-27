from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Protocol

from greetings_bot.aws_runtime import aws_client

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


@dataclass(frozen=True)
class RedriveTaskStatus:
    status: str
    moved: int
    remaining: int

    def __post_init__(self) -> None:
        if self.status not in (
            "RUNNING",
            "COMPLETED",
            "CANCELLING",
            "CANCELLED",
            "FAILED",
        ):
            raise ValueError("unknown redrive status")
        if min(self.moved, self.remaining) < 0:
            raise ValueError("redrive counts must not be negative")

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status.lower(),
            "moved": self.moved,
            "remaining": self.remaining,
        }


class DeliveryAdminOperations(Protocol):
    def summary(self) -> DeliveryQueueSummary:
        ...

    def start_redrive(self, max_rate: int) -> str:
        ...

    def latest_redrive(self) -> Optional[RedriveTaskStatus]:
        ...

    def cancel_redrive(self, task_handle: str) -> None:
        ...


class SqsAdminClient(Protocol):
    def get_queue_attributes(self, **request) -> Mapping[str, object]:
        ...

    def start_message_move_task(self, **request) -> Mapping[str, object]:
        ...

    def list_message_move_tasks(self, **request) -> Mapping[str, object]:
        ...

    def cancel_message_move_task(self, **request) -> Mapping[str, object]:
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

    def latest_redrive(self) -> Optional[RedriveTaskStatus]:
        try:
            response = self.client.list_message_move_tasks(
                SourceArn=self.dead_letter_arn,
                MaxResults=1,
            )
            results = response.get("Results", [])
            if not results:
                return None
            result = results[0]
            return RedriveTaskStatus(
                str(result["Status"]),
                int(result.get("ApproximateNumberOfMessagesMoved", 0)),
                int(result.get("ApproximateNumberOfMessagesToMove", 0)),
            )
        except Exception as error:
            raise DeliveryAdminError("delivery redrive status unavailable") from error

    def cancel_redrive(self, task_handle: str) -> None:
        if not task_handle or len(task_handle) > 1024:
            raise ValueError("invalid redrive task handle")
        try:
            self.client.cancel_message_move_task(TaskHandle=task_handle)
        except Exception as error:
            raise DeliveryAdminError("delivery redrive cancellation unavailable") from error


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
        client = aws_client("sqs")
    return SqsDeliveryAdmin(client, *values)
