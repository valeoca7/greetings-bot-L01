import unittest

from greetings_bot.telegram import (
    Message,
    Reply,
    TelegramUser,
    Update,
    reply_batch,
    reply_payload,
)


class TelegramModelTest(unittest.TestCase):
    def test_represents_a_text_message(self):
        sender = TelegramUser(id=42, first_name="Mira")
        message = Message(id=7, chat_id=42, sender=sender, text="/start")

        update = Update(id=1001, message=message)

        self.assertEqual(update.message.text, "/start")
        self.assertEqual(update.message.sender.first_name, "Mira")

    def test_allows_an_update_without_a_message(self):
        self.assertIsNone(Update(id=1002).message)

    def test_builds_a_send_message_payload(self):
        reply = Reply(chat_id=42, text="Hello, Mira!")

        self.assertEqual(
            reply_payload(reply),
            {"chat_id": 42, "text": "Hello, Mira!"},
        )

    def test_builds_a_reply_batch(self):
        replies = [Reply(chat_id=1, text="One"), Reply(chat_id=2, text="Two")]

        self.assertEqual(
            [{"chat_id": 1, "text": "One"}, {"chat_id": 2, "text": "Two"}],
            reply_batch(replies),
        )


if __name__ == "__main__":
    unittest.main()
