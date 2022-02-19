import unittest

from greetings_bot.app import handle_update
from greetings_bot.telegram import Message, TelegramUser, Update


def text_update(text):
    sender = TelegramUser(id=42, first_name="Mira")
    message = Message(id=7, chat_id=42, sender=sender, text=text)
    return Update(id=1001, message=message)


class AppTest(unittest.TestCase):
    def test_handles_start_command(self):
        self.assertEqual(handle_update(text_update("/start")), "Hello!")

    def test_ignores_other_messages(self):
        self.assertIsNone(handle_update(text_update("hello")))

    def test_ignores_updates_without_messages(self):
        self.assertIsNone(handle_update(Update(id=1002)))


if __name__ == "__main__":
    unittest.main()
