from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    telegram_id: int
    chat_id: int
    first_name: str
