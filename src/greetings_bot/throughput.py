from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ThroughputPolicy:
    dispatch_batch_size: int = 100
    queue_high_watermark: int = 1000

    def __post_init__(self) -> None:
        if not 1 <= self.dispatch_batch_size <= 500:
            raise ValueError("dispatch batch size must be between 1 and 500")
        if not 10 <= self.queue_high_watermark <= 10000:
            raise ValueError("queue high watermark must be between 10 and 10000")


def throughput_from_env(environ: Mapping[str, str]) -> ThroughputPolicy:
    try:
        return ThroughputPolicy(
            int(environ.get("DISPATCH_BATCH_SIZE", "100")),
            int(environ.get("DELIVERY_QUEUE_HIGH_WATERMARK", "1000")),
        )
    except ValueError as error:
        raise ValueError("invalid throughput configuration") from error
