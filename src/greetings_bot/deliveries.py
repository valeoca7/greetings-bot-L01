from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Delivery:
    telegram_id: int
    day: date
