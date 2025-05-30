import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from greetings_bot.admin_handler import (
    AdminLambdaHandler,
    build_default_handler,
    handle_event,
)
from greetings_bot.admin_delivery import SqsDeliveryAdmin
from greetings_bot.dynamo_users import DynamoUserRepository
from greetings_bot.users import User


class AdminHandlerTest(unittest.TestCase):
    def setUp(self):
        self.handler = build_default_handler(
            {"ADMIN_API_TOKEN": "a-long-local-admin-token"}
        )

    def test_serves_an_authorized_stats_request(self):
        self.handler.application.users.save(User(42, 42, "Mira"))

        response = self.handler.handle(
            {
                "rawPath": "/admin/stats",
                "headers": {
                    "authorization": "Bearer a-long-local-admin-token"
                },
                "requestContext": {"http": {"method": "GET"}},
            }
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), {"users": 1})

    def test_rejects_unauthorized_requests(self):
        response = self.handler.handle(
            {"path": "/admin/health", "httpMethod": "GET", "headers": {}}
        )

        self.assertEqual(response["statusCode"], 401)

    def test_lists_filtered_users_through_gateway_event(self):
        self.handler.application.users.save(User(42, 42, "Mira"))
        self.handler.application.users.save(User(7, 7, "Sam", enabled=False))

        response = self.handler.handle(
            {
                "path": "/admin/users",
                "httpMethod": "GET",
                "headers": {
                    "authorization": "Bearer a-long-local-admin-token"
                },
                "queryStringParameters": {"status": "active"},
            }
        )

        body = json.loads(response["body"])
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual([item["id"] for item in body["items"]], [42])

    def test_serves_the_dashboard_through_gateway_event(self):
        self.handler.application.users.save(User(42, 42, "Mira"))
        event = {
            "path": "/admin/dashboard",
            "httpMethod": "GET",
            "headers": {
                "authorization": "Bearer a-long-local-admin-token"
            },
        }

        response = self.handler.handle(event)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            response["headers"]["content-type"], "text/html; charset=utf-8"
        )
        self.assertIn("Greetings Bot Admin", response["body"])

        with patch("greetings_bot.admin_handler._handler", self.handler):
            with self.assertLogs(
                "greetings_bot.admin_handler", level="INFO"
            ) as logs:
                handle_event(event)
        self.assertIn('"action":"dashboard_view"', " ".join(logs.output))

    def test_rejects_malformed_gateway_events(self):
        response = self.handler.handle({})

        self.assertEqual(response["statusCode"], 400)

    def test_requires_an_admin_token(self):
        with self.assertRaises(ValueError):
            build_default_handler({})

    def test_uses_the_configured_user_table(self):
        class Resource:
            def __init__(self):
                self.table = object()

            def Table(self, name):
                self.name = name
                return self.table

        resource = Resource()

        handler = build_default_handler(
            {
                "ADMIN_API_TOKEN": "a-long-local-admin-token",
                "USER_TABLE_NAME": "greetings-data",
            },
            resource,
        )

        self.assertIsInstance(
            handler.application.users, DynamoUserRepository
        )
        self.assertIs(handler.application.users.table, resource.table)
        self.assertEqual(resource.name, "greetings-data")

    def test_builds_configured_delivery_operations(self):
        client = object()

        handler = build_default_handler(
            {
                "ADMIN_API_TOKEN": "a-long-local-admin-token",
                "DELIVERY_QUEUE_URL": "queue-url",
                "DELIVERY_DLQ_URL": "dlq-url",
                "DELIVERY_QUEUE_ARN": "queue-arn",
                "DELIVERY_DLQ_ARN": "dlq-arn",
            },
            sqs_client=client,
        )

        self.assertIsInstance(handler.application.delivery, SqsDeliveryAdmin)
        self.assertIs(handler.application.delivery.client, client)

    def test_logs_status_without_exposing_the_admin_token(self):
        event = {
            "path": "/admin/health",
            "httpMethod": "GET",
            "headers": {
                "authorization": "Bearer a-long-local-admin-token"
            },
        }

        with patch("greetings_bot.admin_handler._handler", self.handler):
            with self.assertLogs(
                "greetings_bot.admin_handler", level="INFO"
            ) as logs:
                response = handle_event(
                    event, SimpleNamespace(aws_request_id="admin-request-1")
                )

        self.assertEqual(response["statusCode"], 200)
        output = " ".join(logs.output)
        self.assertIn('"event":"admin_request_complete"', output)
        self.assertIn('"action":"health_read"', output)
        self.assertIn('"request_id":"admin-request-1"', output)
        self.assertNotIn("a-long-local-admin-token", output)

    def test_audits_user_detail_without_logging_the_user_id(self):
        event = {
            "path": "/admin/users/987654321",
            "httpMethod": "GET",
            "headers": {
                "authorization": "Bearer a-long-local-admin-token"
            },
        }

        with patch("greetings_bot.admin_handler._handler", self.handler):
            with self.assertLogs(
                "greetings_bot.admin_handler", level="WARNING"
            ) as logs:
                handle_event(event)

        output = " ".join(logs.output)
        self.assertIn('"action":"user_detail"', output)
        self.assertNotIn("987654321", output)

    def test_audits_redrive_without_logging_action_body(self):
        event = {
            "path": "/admin/delivery/redrive",
            "httpMethod": "POST",
            "headers": {},
            "body": '{"confirm":"redrive_failed_deliveries","rate":25}',
        }

        with patch("greetings_bot.admin_handler._handler", self.handler):
            with self.assertLogs(
                "greetings_bot.admin_handler", level="WARNING"
            ) as logs:
                handle_event(event)

        output = " ".join(logs.output)
        self.assertIn('"action":"delivery_redrive"', output)
        self.assertNotIn("redrive_failed_deliveries", output)
        self.assertNotIn('"rate"', output)


if __name__ == "__main__":
    unittest.main()
