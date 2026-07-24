from dataclasses import dataclass
from typing import Mapping

from greetings_bot.config_values import integer_value


@dataclass(frozen=True)
class ThroughputPolicy:
    dispatch_batch_size: int = 100
    queue_high_watermark: int = 1000
    profile_page_size: int = 100

    def __post_init__(self) -> None:
        if not 1 <= self.dispatch_batch_size <= 500:
            raise ValueError("dispatch batch size must be between 1 and 500")
        if not 10 <= self.queue_high_watermark <= 10000:
            raise ValueError("queue high watermark must be between 10 and 10000")
        if not 10 <= self.profile_page_size <= 500:
            raise ValueError("profile page size must be between 10 and 500")


def throughput_from_env(environ: Mapping[str, str]) -> ThroughputPolicy:
    return ThroughputPolicy(
        integer_value(environ, "DISPATCH_BATCH_SIZE", 100, 1, 500),
        integer_value(
            environ, "DELIVERY_QUEUE_HIGH_WATERMARK", 1000, 10, 10000
        ),
        integer_value(environ, "PROFILE_SCAN_PAGE_SIZE", 100, 10, 500),
    )
