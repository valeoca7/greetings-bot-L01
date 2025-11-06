import json
import unittest
from datetime import datetime, timezone

from greetings_bot.notes import Note
from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.reminders import Reminder
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.user_data import (
    UserDataExporter,
    UserDataExportError,
    build_user_export,
    serialize_user_export,
)
from greetings_bot.users import InMemoryUserRepository, User


class UserDataExportTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2025, 8, 11, 20, 0, tzinfo=timezone.utc)
        self.user = User(42, 4200, "Mira", timezone="America/Vancouver")

    def test_builds_a_versioned_user_data_document(self):
        note = Note("note-b", 42, "bring an umbrella", self.now)
        reminder = Reminder(
            "reminder-a",
            42,
            4200,
            "call home",
            self.now,
            self.now,
        )

        document = build_user_export(
            self.user, [note], [reminder], self.now
        )

        self.assertEqual(document["schema_version"], 1)
        self.assertEqual(document["profile"]["telegram_id"], 42)
        self.assertEqual(
            document["profile"]["greeting_template_category"], "friendly"
        )
        self.assertEqual(document["notes"][0]["text"], "bring an umbrella")
        self.assertEqual(document["reminders"][0]["text"], "call home")
        self.assertEqual(document["generated_at"], "2025-08-11T20:00:00Z")

    def test_omits_delivery_and_owner_identifiers(self):
        document = build_user_export(self.user, [], [], self.now)

        encoded = serialize_user_export(document)

        self.assertNotIn("chat_id", encoded)
        self.assertNotIn("owner_id", encoded)
        self.assertNotIn("gsi1pk", encoded)
        self.assertNotIn("4200", encoded)

    def test_serializes_unicode_and_items_deterministically(self):
        notes = [
            Note("z-note", 42, "café", self.now),
            Note("a-note", 42, "first", self.now),
        ]

        first = serialize_user_export(
            build_user_export(self.user, notes, [], self.now)
        )
        second = serialize_user_export(
            build_user_export(self.user, reversed(notes), [], self.now)
        )

        self.assertEqual(first, second)
        self.assertEqual(json.loads(first)["notes"][0]["id"], "a-note")
        self.assertIn("café", first)

    def test_requires_timezone_aware_export_time(self):
        with self.assertRaises(ValueError):
            build_user_export(
                self.user, [], [], datetime(2025, 8, 11, 20, 0)
            )

    def test_rejects_records_owned_by_someone_else(self):
        other_note = Note("private", 7, "not Mira's", self.now)
        other_reminder = Reminder(
            "private", 7, 700, "not Mira's", self.now, self.now
        )

        for notes, reminders in (
            ([other_note], []),
            ([], [other_reminder]),
        ):
            with self.subTest(notes=notes, reminders=reminders):
                with self.assertRaises(ValueError):
                    build_user_export(
                        self.user, notes, reminders, self.now
                    )


class UserDataExporterTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2025, 8, 14, 3, 0, tzinfo=timezone.utc)
        self.users = InMemoryUserRepository()
        self.notes = InMemoryNoteRepository()
        self.reminders = InMemoryReminderRepository()
        self.users.save(User(42, 4200, "Mira"))

    def test_collects_only_the_requested_users_records(self):
        self.notes.save(Note("mine", 42, "hello", self.now))
        self.notes.save(Note("other", 7, "private", self.now))
        exporter = UserDataExporter(
            self.users, self.notes, self.reminders
        )

        document = json.loads(exporter.export(42, self.now))

        self.assertEqual([item["id"] for item in document["notes"]], ["mine"])
        self.assertNotIn("private", str(document))

    def test_rejects_an_unknown_user(self):
        exporter = UserDataExporter(
            self.users, self.notes, self.reminders
        )

        with self.assertRaises(UserDataExportError):
            exporter.export(7, self.now)

    def test_bounds_each_export_collection(self):
        self.notes.save(Note("one", 42, "first", self.now))
        self.notes.save(Note("two", 42, "second", self.now))
        exporter = UserDataExporter(
            self.users, self.notes, self.reminders, max_items=1
        )

        with self.assertRaises(UserDataExportError):
            exporter.export(42, self.now)


if __name__ == "__main__":
    unittest.main()
