import json
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from greetings_bot.notes import Note
from greetings_bot.note_store import NoteRepository
from greetings_bot.reminders import Reminder
from greetings_bot.reminder_store import ReminderRepository
from greetings_bot.users import User
from greetings_bot.users import UserRepository


EXPORT_SCHEMA_VERSION = 1


class UserDataExportError(RuntimeError):
    pass


class UserDataExporter:
    def __init__(
        self,
        users: UserRepository,
        notes: NoteRepository,
        reminders: ReminderRepository,
        max_items: int = 1000,
    ) -> None:
        if not 1 <= max_items <= 5000:
            raise ValueError("export item limit must be between 1 and 5000")
        self.users = users
        self.notes = notes
        self.reminders = reminders
        self.max_items = max_items

    def export(self, telegram_id: int, generated_at: datetime) -> str:
        user = self.users.get(telegram_id)
        if user is None:
            raise UserDataExportError("user not found")
        notes = self.notes.all_for(telegram_id)
        reminders = self.reminders.all_for(telegram_id)
        if len(notes) > self.max_items or len(reminders) > self.max_items:
            raise UserDataExportError("user export is too large")
        return serialize_user_export(
            build_user_export(user, notes, reminders, generated_at)
        )


def build_user_export(
    user: User,
    notes: Iterable[Note],
    reminders: Iterable[Reminder],
    generated_at: datetime,
) -> Dict[str, object]:
    if generated_at.tzinfo is None:
        raise ValueError("export time must include a timezone")
    note_items = sorted(notes, key=lambda item: item.id)
    reminder_items = sorted(reminders, key=lambda item: item.id)
    if any(note.owner_id != user.telegram_id for note in note_items):
        raise ValueError("export note belongs to another user")
    if any(
        reminder.owner_id != user.telegram_id
        for reminder in reminder_items
    ):
        raise ValueError("export reminder belongs to another user")
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "generated_at": _timestamp(generated_at),
        "profile": _profile(user),
        "notes": [_note(note) for note in note_items],
        "reminders": [
            _reminder(reminder) for reminder in reminder_items
        ],
    }


def serialize_user_export(document: Dict[str, object]) -> str:
    return json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _profile(user: User) -> Dict[str, object]:
    location: Optional[Dict[str, object]] = None
    if user.weather_location is not None:
        location = {
            "name": user.weather_location.name,
            "latitude": user.weather_location.latitude,
            "longitude": user.weather_location.longitude,
        }
    return {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "locale": user.locale,
        "enabled": user.enabled,
        "timezone": user.timezone,
        "greeting_time": user.greeting_time,
        "greeting_days": list(user.greeting_days),
        "quiet_start": user.quiet_start,
        "quiet_end": user.quiet_end,
        "digest_mode": user.digest_mode,
        "weather_location": location,
        "weather_units": user.weather_units,
        "weather_summary": user.weather_summary,
    }


def _note(note: Note) -> Dict[str, object]:
    return {
        "id": note.id,
        "text": note.text,
        "created_at": _timestamp(note.created_at),
    }


def _reminder(reminder: Reminder) -> Dict[str, object]:
    return {
        "id": reminder.id,
        "text": reminder.text,
        "due_at": _timestamp(reminder.due_at),
        "created_at": _timestamp(reminder.created_at),
        "status": reminder.status,
        "recurrence": reminder.recurrence,
        "timezone": reminder.timezone,
    }


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("export dates must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
