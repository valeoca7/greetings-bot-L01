import unittest

from greetings_bot.scheduled_handler import ScheduledGreetingHandler, handle_event
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


if __name__ == "__main__":
    unittest.main()
