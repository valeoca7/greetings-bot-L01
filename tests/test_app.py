import unittest

from greetings_bot.app import Application, handle_update
from greetings_bot.telegram import Message, Reply, TelegramUser, Update
from greetings_bot.users import InMemoryUserRepository


def text_update(text):
    sender = TelegramUser(id=42, first_name="Mira")
    message = Message(id=7, chat_id=42, sender=sender, text=text)
    return Update(id=1001, message=message)


class AppTest(unittest.TestCase):
    def test_application_keeps_its_user_repository(self):
        users = InMemoryUserRepository()
        application = Application(users)

        application.handle(text_update("/start"))

        self.assertIs(application.users, users)
        self.assertEqual(application.users.count(), 1)

    def test_handles_start_command(self):
        reply = handle_update(text_update("/start"))

        self.assertEqual(reply, Reply(chat_id=42, text="Hello, Mira!"))

    def test_handles_help_command(self):
        reply = handle_update(text_update("/help"))

        self.assertEqual(reply.text, "Send /start to get a greeting.")
        self.assertEqual(reply.chat_id, 42)

    def test_ignores_other_messages(self):
        self.assertIsNone(handle_update(text_update("hello")))

    def test_replies_to_unknown_commands(self):
        reply = handle_update(text_update("/weather"))

        self.assertEqual(reply.text, "I don't know that command. Try /help.")

    def test_registers_user_on_start(self):
        users = InMemoryUserRepository()

        handle_update(text_update("/start"), users)

        self.assertEqual(users.get(42).first_name, "Mira")
        self.assertEqual(users.get(42).chat_id, 42)

    def test_handles_register_command(self):
        users = InMemoryUserRepository()

        reply = handle_update(text_update("/register"), users)

        self.assertEqual(reply.text, "Hello, Mira!")
        self.assertIsNotNone(users.get(42))

    def test_does_not_duplicate_an_existing_user(self):
        users = InMemoryUserRepository()

        handle_update(text_update("/start"), users)
        handle_update(text_update("/start"), users)

        self.assertEqual(users.count(), 1)

    def test_logs_command_without_its_arguments(self):
        with self.assertLogs("greetings_bot.app", level="INFO") as logs:
            handle_update(text_update("/start private-text"))

        self.assertIn("start command from user 42", logs.output[0])
        self.assertNotIn("private-text", logs.output[0])

    def test_ignores_updates_without_messages(self):
        self.assertIsNone(handle_update(Update(id=1002)))


if __name__ == "__main__":
    unittest.main()
