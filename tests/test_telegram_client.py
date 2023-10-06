import json
import unittest

from greetings_bot.delivery_queue import DeliveryMessage
from greetings_bot.telegram_client import TelegramBotClient


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class FakeOpener:
    def __init__(self):
        self.request = None
        self.timeout = None

    def __call__(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return FakeResponse()


class TelegramBotClientTest(unittest.TestCase):
    def test_posts_delivery_message(self):
        opener = FakeOpener()
        client = TelegramBotClient("secret", opener)

        client.send(DeliveryMessage("delivery-1", 42, "Hello", "greeting"))

        self.assertTrue(opener.request.full_url.endswith("/botsecret/sendMessage"))
        self.assertEqual(
            json.loads(opener.request.data), {"chat_id": 42, "text": "Hello"}
        )
        self.assertEqual(opener.timeout, 5)


if __name__ == "__main__":
    unittest.main()
