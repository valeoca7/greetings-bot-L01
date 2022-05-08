from dataclasses import dataclass
from typing import Dict, Optional, Protocol


@dataclass(frozen=True)
class User:
    telegram_id: int
    chat_id: int
    first_name: str
    enabled: bool = True


def normalize_first_name(first_name: str) -> str:
    return first_name.strip() or "friend"


class UserRepository(Protocol):
    def save(self, user: User) -> None:
        ...

    def get(self, telegram_id: int) -> Optional[User]:
        ...

    def count(self) -> int:
        ...


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users: Dict[int, User] = {}

    def save(self, user: User) -> None:
        self._users[user.telegram_id] = user

    def get(self, telegram_id: int) -> Optional[User]:
        return self._users.get(telegram_id)

    def count(self) -> int:
        return len(self._users)
