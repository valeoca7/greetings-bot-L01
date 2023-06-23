import unittest
from datetime import datetime, timezone

from greetings_bot.app import Application, handle_update
from greetings_bot.clock import FixedClock
from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.reminder_store import InMemoryReminderRepository
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

    def test_application_keeps_its_note_repository(self):
        notes = InMemoryNoteRepository()

        application = Application(notes=notes)

        self.assertIs(application.notes, notes)

    def test_application_keeps_its_reminder_repository(self):
        reminders = InMemoryReminderRepository()

        application = Application(reminders=reminders)

        self.assertIs(application.reminders, reminders)

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
            "/name [name] - show or change greeting name\n"
            "/note add <text> - save a note\n"
            "/notes - list saved notes\n"
            "/remind YYYY-MM-DD HH:MM <text> - set a reminder\n"
            "/remind every day HH:MM <text> - repeat daily\n"
            "/remind every <weekday> HH:MM <text> - repeat weekly\n"
            "/reminders - list reminders",
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

    def test_adds_note(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)

        reply = handle_update(text_update("/note add Call the dentist"), users, notes)

        self.assertTrue(reply.text.startswith("Saved note "))
        self.assertEqual(notes.all_for(42)[0].text, "Call the dentist")

    def test_requires_registration_before_saving_note(self):
        notes = InMemoryNoteRepository()

        reply = handle_update(
            text_update("/note add Private text"),
            InMemoryUserRepository(),
            notes,
        )

        self.assertEqual(reply.text, "You are not registered. Send /register first.")
        self.assertEqual(notes.all_for(42), [])

    def test_lists_notes(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)
        saved = handle_update(text_update("/note add Buy tea"), users, notes)
        note_id = saved.text.split()[2].rstrip(".")

        reply = handle_update(text_update("/notes"), users, notes)

        self.assertEqual(reply.text, "{}: Buy tea".format(note_id))

    def test_reports_empty_note_list(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)

        reply = handle_update(text_update("/notes"), users, notes)

        self.assertEqual(reply.text, "You have no notes.")

    def test_shows_note_by_id(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)
        saved = handle_update(text_update("/note add Buy green tea"), users, notes)
        note_id = saved.text.split()[2].rstrip(".")

        reply = handle_update(text_update("/note " + note_id), users, notes)

        self.assertEqual(reply.text, "Buy green tea")

    def test_hides_unknown_note(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/note missing"), users)

        self.assertEqual(reply.text, "Note not found.")

    def test_deletes_note(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)
        saved = handle_update(text_update("/note add Temporary"), users, notes)
        note_id = saved.text.split()[2].rstrip(".")

        reply = handle_update(
            text_update("/note delete " + note_id), users, notes
        )

        self.assertEqual(reply.text, "Note deleted.")
        self.assertEqual(notes.all_for(42), [])

    def test_reports_unknown_note_on_delete(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/note delete missing"), users)

        self.assertEqual(reply.text, "Note not found.")

    def test_explains_note_command(self):
        reply = handle_update(text_update("/note"))

        self.assertEqual(
            reply.text,
            "Use /note add <text>, /note <id>, or /note delete <id>.",
        )

    def test_creates_one_time_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(
            text_update("/remind 2023-04-01 09:30 Call home"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 3, 17, 18, 0, tzinfo=timezone.utc)),
        )

        self.assertIn("set for 2023-04-01 09:30", reply.text)
        self.assertEqual(reminders.all_for(42)[0].text, "Call home")

    def test_lists_reminders(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        clock = FixedClock(datetime(2023, 3, 17, 18, 0, tzinfo=timezone.utc))
        handle_update(
            text_update("/remind 2023-04-01 09:30 Call home"),
            users,
            reminders=reminders,
            clock=clock,
        )

        reply = handle_update(
            text_update("/reminders"), users, reminders=reminders
        )

        self.assertIn("2023-04-01 09:30 Call home (pending)", reply.text)

    def test_reports_empty_reminder_list(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/reminders"), users)

        self.assertEqual(reply.text, "You have no reminders.")

    def test_shows_owned_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind 2023-07-01 09:30 Call home"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 6, 15, 18, 0, tzinfo=timezone.utc)),
        )
        reminder_id = created.text.split()[1]

        reply = handle_update(
            text_update("/reminder " + reminder_id),
            users,
            reminders=reminders,
        )

        self.assertIn("Call home\nDue: 2023-07-01 09:30", reply.text)

    def test_hides_unknown_reminder(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/reminder missing"), users)

        self.assertEqual(reply.text, "Reminder not found.")

    def test_edits_reminder_text(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind 2023-07-01 09:30 Old text"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 6, 19, 18, 0, tzinfo=timezone.utc)),
        )
        reminder_id = created.text.split()[1]

        reply = handle_update(
            text_update("/reminder edit {} New text".format(reminder_id)),
            users,
            reminders=reminders,
        )

        self.assertEqual(reply.text, "Reminder updated.")
        self.assertEqual(reminders.get(42, reminder_id).text, "New text")

    def test_pauses_and_resumes_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind every day 09:30 Stretch"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 6, 20, 18, 0, tzinfo=timezone.utc)),
        )
        reminder_id = created.text.split()[2]

        paused = handle_update(
            text_update("/reminder pause " + reminder_id),
            users,
            reminders=reminders,
        )
        resumed = handle_update(
            text_update("/reminder resume " + reminder_id),
            users,
            reminders=reminders,
        )

        self.assertEqual(paused.text, "Reminder paused.")
        self.assertEqual(resumed.text, "Reminder resumed.")
        self.assertEqual(reminders.get(42, reminder_id).status, "pending")

    def test_creates_daily_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(
            text_update("/remind every day 09:00 Drink water"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 5, 8, 18, 0, tzinfo=timezone.utc)),
        )

        self.assertTrue(reply.text.startswith("Daily reminder "))
        self.assertEqual(reminders.all_for(42)[0].recurrence, "daily")

    def test_creates_weekly_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(
            text_update("/remind every monday 09:00 Plan week"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 5, 8, 18, 0, tzinfo=timezone.utc)),
        )

        self.assertTrue(reply.text.startswith("Weekly reminder "))
        self.assertEqual(reminders.all_for(42)[0].recurrence, "weekly")

    def test_rejects_long_note_text(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/note add " + "x" * 501), users)

        self.assertEqual(
            reply.text,
            "Note text must be 500 characters or shorter.",
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
