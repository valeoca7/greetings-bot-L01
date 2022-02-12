import unittest

from greetings_bot.telegram import Message, TelegramUser, Update


class TelegramModelTest(unittest.TestCase):
    def test_represents_a_text_message(self):
        sender = TelegramUser(id=42, first_name="Mira")
        message = Message(id=7, chat_id=42, sender=sender, text="/start")

        update = Update(id=1001, message=message)

        self.assertEqual(update.message.text, "/start")
        self.assertEqual(update.message.sender.first_name, "Mira")

    def test_allows_an_update_without_a_message(self):
        self.assertIsNone(Update(id=1002).message)


if __name__ == "__main__":
    unittest.main()
