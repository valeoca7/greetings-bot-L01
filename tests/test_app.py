import unittest

from greetings_bot.app import Application, handle_update
from greetings_bot.telegram import Message, Reply, TelegramUser, Update
from greetings_bot.users import InMemoryUserRepository


def text_update(text, language_code=None):
    sender = TelegramUser(
        id=42,
        first_name="Mira",
        language_code=language_code,
    )
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

        self.assertEqual(
            reply.text,
            "Available commands:\n"
            "/start - get a greeting\n"
            "/register - create a profile\n"
            "/me - show your profile\n"
            "/time [HH:MM] - show or change greeting time\n"
            "/timezone [area/name] - show or change timezone\n"
            "/quiet [start end|off] - manage quiet hours\n"
            "/name [name] - show or change greeting name",
        )
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

    def test_uses_telegram_language_during_registration(self):
        users = InMemoryUserRepository()

        handle_update(text_update("/register", "uk"), users)

        self.assertEqual(users.get(42).locale, "uk")

    def test_handles_register_command(self):
        users = InMemoryUserRepository()

        reply = handle_update(text_update("/register"), users)

        self.assertEqual(reply.text, "Thanks, Mira. You are registered.")
        self.assertIsNotNone(users.get(42))

    def test_does_not_duplicate_an_existing_user(self):
        users = InMemoryUserRepository()

        handle_update(text_update("/start"), users)
        handle_update(text_update("/start"), users)

        self.assertEqual(users.count(), 1)

    def test_reports_an_existing_registration(self):
        users = InMemoryUserRepository()

        handle_update(text_update("/register"), users)
        reply = handle_update(text_update("/register"), users)

        self.assertEqual(reply.text, "You are already registered, Mira.")
        self.assertEqual(users.count(), 1)

    def test_shows_current_user(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/me"), users)

        self.assertEqual(
            reply.text,
            "Name: Mira\nTelegram ID: 42\nLanguage: en\n"
            "Greeting time: 09:00\nTimezone: UTC\nGreetings: on",
        )

    def test_reports_missing_profile(self):
        reply = handle_update(text_update("/me"), InMemoryUserRepository())

        self.assertEqual(
            reply.text,
            "You are not registered. Send /register first.",
        )

    def test_shows_greeting_time(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/time"), users)

        self.assertEqual(reply.text, "Your greeting time is 09:00.")

    def test_changes_greeting_time(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/time 18:30"), users)

        self.assertEqual(reply.text, "Greeting time changed to 18:30.")
        self.assertEqual(users.get(42).greeting_time, "18:30")

    def test_rejects_invalid_greeting_time(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/time evening"), users)

        self.assertEqual(
            reply.text,
            "Use time in HH:MM format, for example 08:30.",
        )
        self.assertEqual(users.get(42).greeting_time, "09:00")

    def test_shows_timezone(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/timezone"), users)

        self.assertEqual("Your timezone is UTC.", reply.text)

    def test_changes_timezone(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/timezone America/Vancouver"), users)

        self.assertEqual("Timezone changed to America/Vancouver.", reply.text)
        self.assertEqual("America/Vancouver", users.get(42).timezone)

    def test_rejects_unknown_timezone(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/timezone Mars/Base"), users)

        self.assertEqual("Use an IANA timezone such as America/Vancouver.", reply.text)

    def test_sets_quiet_hours(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/quiet 22:00 07:00"), users)

        self.assertEqual("Quiet hours changed to 22:00-07:00.", reply.text)

    def test_shows_disabled_quiet_hours(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/quiet"), users)

        self.assertEqual("Quiet hours are off.", reply.text)

    def test_turns_off_quiet_hours(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        handle_update(text_update("/quiet 22:00 07:00"), users)

        reply = handle_update(text_update("/quiet off"), users)

        self.assertEqual("Quiet hours turned off.", reply.text)
        self.assertIsNone(users.get(42).quiet_start)

    def test_shows_greeting_name(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/name"), users)

        self.assertEqual(reply.text, "Your greeting name is Mira.")

    def test_changes_greeting_name(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/name Mira Jane"), users)

        self.assertEqual(reply.text, "Greeting name changed to Mira Jane.")
        self.assertEqual(users.get(42).first_name, "Mira Jane")

    def test_rejects_long_greeting_name(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/name " + "x" * 41), users)

        self.assertEqual(
            reply.text,
            "Greeting name must be 40 characters or shorter.",
        )

    def test_logs_command_without_its_arguments(self):
        with self.assertLogs("greetings_bot.app", level="INFO") as logs:
            handle_update(text_update("/start private-text"))

        self.assertIn("start command from user 42", logs.output[0])
        self.assertNotIn("private-text", logs.output[0])

    def test_ignores_updates_without_messages(self):
        self.assertIsNone(handle_update(Update(id=1002)))


if __name__ == "__main__":
    unittest.main()
