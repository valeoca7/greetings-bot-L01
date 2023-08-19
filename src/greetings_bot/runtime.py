from typing import Any, Dict, Mapping, Optional, Union

from greetings_bot.app import handle_update
from greetings_bot.event_scheduler import ReminderSchedulePort
from greetings_bot.note_store import NoteRepository
from greetings_bot.reminder_store import ReminderRepository
from greetings_bot.telegram import reply_payload
from greetings_bot.update_parser import parse_update
from greetings_bot.users import UserRepository


def process_payload(
    payload: Mapping[str, Any],
    users: Optional[UserRepository] = None,
    notes: Optional[NoteRepository] = None,
    reminders: Optional[ReminderRepository] = None,
    reminder_scheduler: Optional[ReminderSchedulePort] = None,
) -> Optional[Dict[str, Union[int, str]]]:
    update = parse_update(payload)
    reply = handle_update(
        update,
        users,
        notes,
        reminders,
        reminder_scheduler=reminder_scheduler,
    )
    if reply is None:
        return None
    return reply_payload(reply)
