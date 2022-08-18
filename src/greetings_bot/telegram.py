from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Union


@dataclass(frozen=True)
class TelegramUser:
    id: int
    first_name: str
    language_code: Optional[str] = None


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


@dataclass(frozen=True)
class Reply:
    chat_id: int
    text: str


def reply_payload(reply: Reply) -> Dict[str, Union[int, str]]:
    return {"chat_id": reply.chat_id, "text": reply.text}


def reply_batch(replies: Iterable[Reply]) -> List[Dict[str, Union[int, str]]]:
    return [reply_payload(reply) for reply in replies]
