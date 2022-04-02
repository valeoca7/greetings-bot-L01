import json
from pathlib import Path
from typing import Any, Mapping

from greetings_bot.telegram import Message, TelegramUser, Update


class UpdateParseError(ValueError):
    pass


def load_update(path: Path) -> Update:
    with path.open() as update_file:
        return parse_update(json.load(update_file))


def parse_update(payload: Mapping[str, Any]) -> Update:
    try:
        update_id = int(payload["update_id"])
        message_payload = payload.get("message")
        if message_payload is None:
            return Update(id=update_id)

        sender_payload = message_payload["from"]
        sender = TelegramUser(
            id=int(sender_payload["id"]),
            first_name=str(sender_payload["first_name"]),
        )
        message = Message(
            id=int(message_payload["message_id"]),
            chat_id=int(message_payload["chat"]["id"]),
            sender=sender,
            text=message_payload.get("text"),
        )
        return Update(id=update_id, message=message)
    except (KeyError, TypeError, ValueError) as error:
        raise UpdateParseError("invalid update payload") from error
