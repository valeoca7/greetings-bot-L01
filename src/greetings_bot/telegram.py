from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TelegramUser:
    id: int
    first_name: str


@dataclass(frozen=True)
class Message:
    id: int
    chat_id: int
    sender: TelegramUser
    text: Optional[str] = None


@dataclass(frozen=True)
class Update:
    id: int
    message: Optional[Message] = None
