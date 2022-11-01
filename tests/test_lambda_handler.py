import unittest

from greetings_bot.lambda_handler import WebhookHandler, handle_event
from greetings_bot.users import InMemoryUserRepository


class LambdaHandlerTest(unittest.TestCase):
    def test_acknowledges_gateway_event(self):
        response = handle_event({"body": '{"update_id": 1}'})

        self.assertEqual(response, {"statusCode": 200, "body": ""})

    def test_processes_telegram_command(self):
        handler = WebhookHandler(InMemoryUserRepository())
        body = (
            '{"update_id":1,"message":{"message_id":2,'
            '"from":{"id":42,"first_name":"Mira"},'
            '"chat":{"id":42},"text":"/start"}}'
        )

        response = handler.handle({"body": body})

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Hello, Mira!", response["body"])

    def test_rejects_event_without_body(self):
        response = WebhookHandler(InMemoryUserRepository()).handle({})

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response["body"], "request body is required")

    def test_rejects_incomplete_telegram_update(self):
        response = WebhookHandler(InMemoryUserRepository()).handle(
            {"body": '{"message": {}}'}
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response["body"], "invalid update payload")


if __name__ == "__main__":
    unittest.main()
