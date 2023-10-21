import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from greetings_bot.dynamo_users import DynamoUserRepository
from greetings_bot.dynamo_notes import DynamoNoteRepository
from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.lambda_handler import (
    WebhookHandler,
    build_default_handler,
    handle_event,
)
from greetings_bot.users import InMemoryUserRepository


class LambdaHandlerTest(unittest.TestCase):
    def test_acknowledges_gateway_event(self):
        with self.assertLogs("greetings_bot.lambda_handler", level="INFO") as logs:
            response = handle_event(
                {"body": '{"update_id": 1}'},
                SimpleNamespace(aws_request_id="request-123"),
            )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["body"], "")
        self.assertEqual(response["headers"]["content-type"], "application/json")
        payload = json.loads(logs.output[0].split(":", 2)[-1])
        self.assertEqual(payload["event"], "webhook_received")
        self.assertEqual(payload["request_id"], "request-123")

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
        self.assertEqual(
            json.loads(response["body"]), {"error": "request body is required"}
        )

    def test_rejects_incomplete_telegram_update(self):
        response = WebhookHandler(InMemoryUserRepository()).handle(
            {"body": '{"message": {}}'}
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            json.loads(response["body"]), {"error": "invalid update payload"}
        )

    def test_handles_sample_gateway_event(self):
        event = json.loads(Path("events/webhook.json").read_text())

        response = WebhookHandler(InMemoryUserRepository()).handle(event)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Hello, Mira!", response["body"])

    def test_uses_configured_dynamo_table(self):
        class Resource:
            def Table(self, name):
                self.name = name
                return object()

        resource = Resource()

        handler = build_default_handler(
            {"USER_TABLE_NAME": "greetings-users"}, resource
        )

        self.assertIsInstance(handler.users, DynamoUserRepository)
        self.assertIsInstance(handler.notes, DynamoNoteRepository)
        self.assertIsInstance(handler.reminders, DynamoReminderRepository)
        self.assertIs(handler.users.table, handler.notes.table)
        self.assertIs(handler.users.table, handler.reminders.table)
        self.assertEqual(resource.name, "greetings-users")


if __name__ == "__main__":
    unittest.main()
