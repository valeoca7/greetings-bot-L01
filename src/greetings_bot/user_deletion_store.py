from typing import Dict, Optional, Protocol

from greetings_bot.user_deletion import DeletionRequest


class DeletionRequestRepository(Protocol):
    def save(self, request: DeletionRequest) -> None:
        ...

    def get(self, telegram_id: int) -> Optional[DeletionRequest]:
        ...


class InMemoryDeletionRequestRepository:
    def __init__(self) -> None:
        self._requests: Dict[int, DeletionRequest] = {}

    def save(self, request: DeletionRequest) -> None:
        self._requests[request.telegram_id] = request

    def get(self, telegram_id: int) -> Optional[DeletionRequest]:
        return self._requests.get(telegram_id)
