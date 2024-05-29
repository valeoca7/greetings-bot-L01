import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from greetings_bot.dynamo_deliveries import DynamoDeliveryLedger
from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import Reminder
from greetings_bot.open_meteo import OpenMeteoWeatherProvider


class FakeQueue:
    def __init__(self):
        self.messages = []

    def enqueue(self, message):
        self.messages.append(message)
from greetings_bot.scheduled_handler import (
    ScheduledGreetingHandler,
    build_default_handler,
    handle_event,
)
from greetings_bot.users import InMemoryUserRepository, User
from greetings_bot.weather import DailyForecast, WeatherLocation


class FakeWeatherProvider:
    def daily_forecast(self, location, forecast_date):
        return DailyForecast(forecast_date, 5, 12, "clear", 10)


class ScheduledGreetingHandlerTest(unittest.TestCase):
    def test_adds_weather_to_an_opted_in_greeting(self):
        users = InMemoryUserRepository()
        users.save(
            User(
                42,
                84,
                "Mira",
                greeting_time="10:00",
                weather_location=WeatherLocation("Vancouver", 49.2, -123.1),
                weather_summary=True,
                digest_mode="daily",
            )
        )
        handler = ScheduledGreetingHandler(
            users, weather_provider=FakeWeatherProvider()
        )

        replies = handler.handle({"time": "2024-05-10T10:00:00Z"})

        self.assertEqual(len(replies), 1)
        self.assertIn("Good day, Mira!", replies[0]["text"])
        self.assertIn("Vancouver: clear, 5-12°C", replies[0]["text"])

    def test_returns_due_telegram_payloads(self):
        users = InMemoryUserRepository()
        users.save(User(42, 84, "Mira", greeting_time="10:00"))
        handler = ScheduledGreetingHandler(users)

        replies = handler.handle({"time": "2023-01-12T10:00:00Z"})

        self.assertEqual(replies, [{"chat_id": 84, "text": "Good day, Mira!"}])

    def test_lambda_entry_point_accepts_empty_repository(self):
        event = {"id": "schedule-2", "time": "2023-01-12T10:00:00Z"}

        with self.assertLogs("greetings_bot.scheduled_handler", level="INFO") as logs:
            self.assertEqual(handle_event(event), [])

        self.assertTrue(any('"request_id":"schedule-2"' in line for line in logs.output))
        self.assertTrue(any('"Prepared":0' in line for line in logs.output))

    def test_builds_cloud_handler_with_shared_table(self):
        class Resource:
            def Table(self, name):
                self.name = name
                return object()

        resource = Resource()

        handler = build_default_handler({"USER_TABLE_NAME": "data"}, resource)

        self.assertEqual(resource.name, "data")
        self.assertIsInstance(handler.deliveries, DynamoDeliveryLedger)
        self.assertIsInstance(handler.reminders, DynamoReminderRepository)
        self.assertIs(handler.users.table, handler.deliveries.table)
        self.assertIs(handler.users.table, handler.reminders.table)
        self.assertIsInstance(handler.weather_provider, OpenMeteoWeatherProvider)

    def test_reads_dispatch_batch_size(self):
        handler = build_default_handler({"DISPATCH_BATCH_SIZE": "25"})

        self.assertEqual(handler.max_batch, 25)

    def test_disables_polled_reminders_for_targeted_delivery(self):
        handler = build_default_handler({"TARGETED_REMINDERS": "true"})

        self.assertFalse(handler.include_reminders)

    def test_accepts_local_scheduled_event(self):
        event = json.loads(Path("events/scheduled.json").read_text())

        replies = ScheduledGreetingHandler(InMemoryUserRepository()).handle(event)

        self.assertEqual(replies, [])

    def test_includes_due_reminders(self):
        reminders = InMemoryReminderRepository()
        reminders.save(
            Reminder(
                "abcd1234", 42, 84, "Call home",
                datetime(2023, 4, 12, 18, 0, tzinfo=timezone.utc),
                datetime(2023, 4, 1, 18, 0, tzinfo=timezone.utc),
            )
        )
        handler = ScheduledGreetingHandler(
            InMemoryUserRepository(), reminders=reminders
        )

        replies = handler.handle({"time": "2023-04-12T18:00:00Z"})

        self.assertEqual(replies, [{"chat_id": 84, "text": "Reminder: Call home"}])

    def test_enqueues_scheduled_greeting(self):
        users = InMemoryUserRepository()
        users.save(User(42, 84, "Mira", greeting_time="10:00"))
        queue = FakeQueue()
        handler = ScheduledGreetingHandler(users, queue=queue)

        handler.handle({"time": "2023-09-21T10:00:00Z"})

        self.assertEqual(len(queue.messages), 1)
        self.assertEqual(queue.messages[0].kind, "greeting")
        self.assertEqual(queue.messages[0].id, "greeting-84-202309211000")


if __name__ == "__main__":
    unittest.main()
