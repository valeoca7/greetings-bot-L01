from dataclasses import dataclass
from typing import Mapping

from greetings_bot.config_values import integer_value


@dataclass(frozen=True)
class RetentionPolicy:
    delivery_days: int = 90
    receipt_days: int = 14

    def __post_init__(self) -> None:
        if not 7 <= self.delivery_days <= 365:
            raise ValueError("delivery retention must be between 7 and 365 days")
        if not 1 <= self.receipt_days <= 30:
            raise ValueError("receipt retention must be between 1 and 30 days")


def retention_from_env(environ: Mapping[str, str]) -> RetentionPolicy:
    return RetentionPolicy(
        integer_value(environ, "DELIVERY_HISTORY_DAYS", 90, 7, 365),
        integer_value(environ, "DELIVERY_RECEIPT_DAYS", 14, 1, 30),
    )
