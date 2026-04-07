import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from greetings_bot.dynamo_users import DynamoUserRepository
from greetings_bot.dynamo_notes import DynamoNoteRepository
from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.dynamo_information_quota import DynamoInformationQuota
from greetings_bot.lambda_handler import (
    WebhookHandler,
    build_default_handler,
    handle_event,
)
from greetings_bot.information_quota import InMemoryInformationQuota
from greetings_bot.users import InMemoryUserRepository
from greetings_bot.weather_cache import CachingWeatherProvider


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
        complete = json.loads(logs.output[1].split(":", 2)[-1])
        self.assertEqual(complete["event"], "webhook_complete")
        self.assertEqual(complete["status_code"], 200)
        self.assertTrue(any('"Requests":1' in line for line in logs.output))
        self.assertTrue(any('"ClientError":0' in line for line in logs.output))

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
        with self.assertLogs("greetings_bot.lambda_handler", level="WARNING") as logs:
            response = handle_event({})

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            json.loads(response["body"]), {"error": "request body is required"}
        )
        self.assertTrue(any('"status_code":400' in line for line in logs.output))

    def test_rejects_incomplete_telegram_update(self):
        response = WebhookHandler(InMemoryUserRepository()).handle(
            {"body": '{"message": {}}'}
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            json.loads(response["body"]), {"error": "invalid update payload"}
        )

    def test_checks_the_webhook_secret_before_parsing_the_body(self):
        handler = build_default_handler(
            {"TELEGRAM_WEBHOOK_SECRET": "local-secret_123"}
        )

        rejected = handler.handle({"body": "private invalid body"})
        accepted = handler.handle(
            {
                "headers": {
                    "X-Telegram-Bot-Api-Secret-Token": "local-secret_123"
                },
                "body": '{"update_id":1}',
            }
        )

        self.assertEqual(rejected["statusCode"], 403)
        self.assertEqual(json.loads(rejected["body"]), {"error": "forbidden"})
        self.assertEqual(accepted["statusCode"], 200)

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
        self.assertIsInstance(handler.weather_provider, CachingWeatherProvider)
        self.assertIs(handler.weather_provider.cache.table, handler.users.table)

    def test_reads_information_feature_flag(self):
        client = object()

        handler = build_default_handler(
            {
                "INFO_REQUESTS_ENABLED": "true",
                "INFO_WEEKLY_LIMIT": "9",
            },
            bedrock_client=client,
        )

        self.assertTrue(handler.information_enabled)
        self.assertIs(handler.information_service.provider.client, client)
        self.assertIsInstance(handler.information_quota, InMemoryInformationQuota)
        self.assertEqual(handler.information_weekly_limit, 9)
        self.assertIs(
            handler.information_service.usage_meter,
            handler.weather_provider.usage_meter,
        )

    def test_uses_the_shared_table_for_information_quota(self):
        class Resource:
            def __init__(self):
                self.table = object()

            def Table(self, name):
                return self.table

        resource = Resource()

        handler = build_default_handler(
            {
                "USER_TABLE_NAME": "data",
                "INFO_REQUESTS_ENABLED": "true",
            },
            resource,
            object(),
        )

        self.assertIsInstance(handler.information_quota, DynamoInformationQuota)
        self.assertIs(handler.information_quota.table, resource.table)

    def test_answers_information_request_through_bedrock_adapter(self):
        class Body:
            def read(self):
                return b'{"results":[{"outputText":"Octopuses have three hearts."}]}'

        class Client:
            def invoke_model(self, **request):
                self.request = request
                return {"body": Body()}

        client = Client()
        handler = build_default_handler(
            {"INFO_REQUESTS_ENABLED": "true"}, bedrock_client=client
        )

        handler.handle({"body": self._message_body("/start")})
        response = handler.handle({"body": self._message_body("/ask fact")})

        self.assertIn("Octopuses have three hearts.", response["body"])
        self.assertEqual(
            client.request["modelId"], "amazon.titan-text-lite-v1"
        )

    @staticmethod
    def _message_body(text):
        return json.dumps(
            {
                "update_id": 1,
                "message": {
                    "message_id": 2,
                    "from": {"id": 42, "first_name": "Mira"},
                    "chat": {"id": 42},
                    "text": text,
                },
            }
        )


if __name__ == "__main__":
    unittest.main()
