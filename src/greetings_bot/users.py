from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence, Tuple

EVERY_DAY = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@dataclass(frozen=True)
class User:
    telegram_id: int
    chat_id: int
    first_name: str
    locale: str = "en"
    greeting_time: str = "09:00"
    enabled: bool = True
    timezone: str = "UTC"
    quiet_start: Optional[str] = None
    quiet_end: Optional[str] = None
    greeting_days: Tuple[str, ...] = EVERY_DAY
    digest_mode: str = "off"


def user_to_dict(user: User) -> Dict[str, object]:
    return {
        "telegram_id": user.telegram_id,
        "chat_id": user.chat_id,
        "first_name": user.first_name,
        "locale": user.locale,
        "greeting_time": user.greeting_time,
        "enabled": user.enabled,
        "timezone": user.timezone,
        "quiet_start": user.quiet_start,
        "quiet_end": user.quiet_end,
        "greeting_days": list(user.greeting_days),
        "digest_mode": user.digest_mode,
    }


def user_from_dict(data: Mapping[str, Any]) -> User:
    return User(
        telegram_id=int(data["telegram_id"]),
        chat_id=int(data["chat_id"]),
        first_name=str(data["first_name"]),
        locale=str(data.get("locale", "en")),
        greeting_time=str(data.get("greeting_time", "09:00")),
        enabled=bool(data.get("enabled", True)),
        timezone=str(data.get("timezone", "UTC")),
        quiet_start=data.get("quiet_start"),
        quiet_end=data.get("quiet_end"),
        greeting_days=tuple(data.get("greeting_days", EVERY_DAY)),
        digest_mode=str(data.get("digest_mode", "off")),
    )


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

    def all(self) -> Sequence[User]:
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

    def all(self) -> Sequence[User]:
        return [self._users[user_id] for user_id in sorted(self._users)]
