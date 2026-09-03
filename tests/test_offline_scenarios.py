import unittest
from datetime import datetime, timezone

from greetings_bot.app import Application
from greetings_bot.clock import FixedClock
from greetings_bot.delivery_queue import message_to_body
from greetings_bot.information import InformationProviderError, InformationService
from greetings_bot.information_quota import InMemoryInformationQuota
from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.queue_worker import DeliveryQueueWorker, InMemoryDeliveryReceiptLedger
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.scheduled_handler import ScheduledGreetingHandler
from greetings_bot.telegram import Message, TelegramUser, Update
from greetings_bot.users import InMemoryUserRepository
from greetings_bot.weather import WeatherProviderError


class CollectingQueue:
    def __init__(self):
        self.messages = []

    def depth(self):
        return 0

    def enqueue(self, message):
        self.messages.append(message)

    def enqueue_many(self, messages):
        self.messages.extend(messages)


class CollectingSender:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


class FailingWeatherProvider:
    def __init__(self):
        self.calls = 0

    def daily_forecast(self, location, forecast_date):
        self.calls += 1
        raise WeatherProviderError("offline")


class FailingInformationProvider:
    def __init__(self):
        self.calls = 0

    def answer(self, request):
        self.calls += 1
        raise InformationProviderError("offline")


class OfflineScenarioTest(unittest.TestCase):
    def test_user_changes_reach_scheduled_queue_delivery(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        reminders = InMemoryReminderRepository()
        clock = FixedClock(datetime(2026, 9, 2, 9, 0, tzinfo=timezone.utc))
        app = Application(users, notes, reminders, clock)

        self._command(app, "/register")
        self._command(app, "/timezone UTC")
        self._command(app, "/time 10:00")
        self._command(app, "/style brief")
        self._command(app, "/note add bring the blue folder")
        self._command(app, "/remind 2026-09-02 10:00 call home")

        queue = CollectingQueue()
        ScheduledGreetingHandler(
            users,
            reminders=reminders,
            queue=queue,
        ).handle({"time": "2026-09-02T10:00:00Z"})

        self.assertEqual(notes.all_for(42)[0].text, "bring the blue folder")
        self.assertEqual(len(queue.messages), 2)
        sender = CollectingSender()
        event = {
            "Records": [
                {
                    "messageId": "message-{}".format(index),
                    "body": message_to_body(message),
                }
                for index, message in enumerate(queue.messages)
            ]
        }

        result = DeliveryQueueWorker(
            sender, InMemoryDeliveryReceiptLedger()
        ).handle(event)

        self.assertEqual(result, {"batchItemFailures": []})
        self.assertEqual(len(sender.messages), 2)
        self.assertTrue(any(message.kind == "greeting" for message in sender.messages))
        self.assertTrue(any("call home" in message.text for message in sender.messages))

    def test_provider_failures_keep_user_data_and_return_short_fallbacks(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        weather = FailingWeatherProvider()
        information = FailingInformationProvider()
        app = Application(
            users,
            notes,
            clock=FixedClock(datetime(2026, 9, 3, 18, 0, tzinfo=timezone.utc)),
            weather_provider=weather,
            information_service=InformationService(information),
            information_enabled=True,
            information_quota=InMemoryInformationQuota(),
        )
        self._command(app, "/register")
        self._command(app, "/note add keep this text")
        self._command(app, "/location 49.2 -123.1 Vancouver")

        weather_reply = self._command(app, "/weather")
        information_reply = self._command(app, "/ask fact")

        self.assertEqual(weather_reply.text, "Weather is temporarily unavailable.")
        self.assertEqual(
            information_reply.text, "Information service is temporarily unavailable."
        )
        self.assertEqual(weather.calls, 1)
        self.assertEqual(information.calls, 1)
        self.assertEqual(notes.all_for(42)[0].text, "keep this text")

    @staticmethod
    def _command(app, text):
        return app.handle(
            Update(1, Message(1, 84, TelegramUser(42, "Mira", "en"), text))
        )


if __name__ == "__main__":
    unittest.main()
