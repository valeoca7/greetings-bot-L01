from dataclasses import dataclass
from typing import Dict, Optional, Protocol


@dataclass(frozen=True)
class User:
    telegram_id: int
    chat_id: int
    first_name: str
    locale: str = "en"
    greeting_time: str = "09:00"
    enabled: bool = True


def user_to_dict(user: User) -> Dict[str, object]:
    return {
        "telegram_id": user.telegram_id,
        "chat_id": user.chat_id,
        "first_name": user.first_name,
        "locale": user.locale,
        "greeting_time": user.greeting_time,
        "enabled": user.enabled,
    }


def normalize_first_name(first_name: str) -> str:
    return first_name.strip() or "friend"


def normalize_locale(locale: Optional[str]) -> str:
    if not locale:
        return "en"
    return locale.replace("_", "-").split("-", 1)[0].lower()


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
