from dataclasses import dataclass
from datetime import date
from typing import List, Protocol


@dataclass(frozen=True)
class Delivery:
    telegram_id: int
    day: date


class DeliveryLedger(Protocol):
    def contains(self, delivery: Delivery) -> bool:
        ...

    def record(self, delivery: Delivery) -> None:
        ...


class InMemoryDeliveryLedger:
    def __init__(self) -> None:
        self._deliveries: List[Delivery] = []

    def contains(self, delivery: Delivery) -> bool:
        return delivery in self._deliveries

    def record(self, delivery: Delivery) -> None:
        if not self.contains(delivery):
            self._deliveries.append(delivery)
