import unittest

from greetings_bot.dynamo_deliveries import DynamoDeliveryLedger
from greetings_bot.scheduled_handler import (
    ScheduledGreetingHandler,
    build_default_handler,
    handle_event,
)
from greetings_bot.users import InMemoryUserRepository, User


class ScheduledGreetingHandlerTest(unittest.TestCase):
    def test_returns_due_telegram_payloads(self):
        users = InMemoryUserRepository()
        users.save(User(42, 84, "Mira", greeting_time="10:00"))
        handler = ScheduledGreetingHandler(users)

        replies = handler.handle({"time": "2023-01-12T10:00:00Z"})

        self.assertEqual(replies, [{"chat_id": 84, "text": "Good day, Mira!"}])

    def test_lambda_entry_point_accepts_empty_repository(self):
        self.assertEqual(handle_event({"time": "2023-01-12T10:00:00Z"}), [])

    def test_builds_cloud_handler_with_shared_table(self):
        class Resource:
            def Table(self, name):
                self.name = name
                return object()

        resource = Resource()

        handler = build_default_handler({"USER_TABLE_NAME": "data"}, resource)

        self.assertEqual(resource.name, "data")
        self.assertIsInstance(handler.deliveries, DynamoDeliveryLedger)
        self.assertIs(handler.users.table, handler.deliveries.table)


if __name__ == "__main__":
    unittest.main()
