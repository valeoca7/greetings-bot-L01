import json
from typing import Callable
from urllib.request import Request, urlopen

from greetings_bot.delivery_queue import DeliveryMessage


class TelegramBotClient:
    def __init__(self, token: str, opener: Callable = urlopen) -> None:
        self.endpoint = "https://api.telegram.org/bot{}/sendMessage".format(token)
        self.opener = opener

    def send(self, message: DeliveryMessage) -> None:
        body = json.dumps(
            {"chat_id": message.chat_id, "text": message.text}
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with self.opener(request, timeout=5) as response:
            if response.status >= 300:
                raise RuntimeError("Telegram send failed")
