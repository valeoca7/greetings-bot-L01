import json
import unittest

from greetings_bot.delivery_queue import DeliveryMessage
from greetings_bot.telegram_client import TelegramBotClient


class FakeResponse:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class FakeOpener:
    def __init__(self, status=200):
        self.request = None
        self.timeout = None
        self.status = status

    def __call__(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return FakeResponse(self.status)


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

    def test_rejects_an_error_response(self):
        client = TelegramBotClient("secret", FakeOpener(status=429))

        with self.assertRaisesRegex(RuntimeError, "Telegram send failed"):
            client.send(DeliveryMessage("delivery-1", 42, "Hello", "greeting"))


if __name__ == "__main__":
    unittest.main()
