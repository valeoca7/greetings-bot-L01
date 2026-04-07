import hmac
import re
from typing import Mapping


SECRET_HEADER = "x-telegram-bot-api-secret-token"
SECRET_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class TelegramWebhookAuthorizer:
    def __init__(self, secret: str) -> None:
        if not 16 <= len(secret) <= 256 or not SECRET_PATTERN.fullmatch(secret):
            raise ValueError("invalid Telegram webhook secret")
        self._secret = secret

    def authorize(self, headers: Mapping[str, str]) -> bool:
        supplied = headers.get(SECRET_HEADER, "")
        return hmac.compare_digest(supplied, self._secret)
