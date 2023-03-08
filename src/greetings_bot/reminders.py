from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

from greetings_bot.users import User


ReminderStatus = Literal["pending", "sent", "cancelled"]


@dataclass(frozen=True)
class Reminder:
    id: str
    owner_id: int
    chat_id: int
    text: str
    due_at: datetime
    created_at: datetime
    status: ReminderStatus = "pending"


def mark_sent(reminder: Reminder) -> Reminder:
    return replace(reminder, status="sent")


def create_reminder(
    user: User,
    local_date: str,
    local_time: str,
    text: str,
    now: datetime,
) -> Reminder:
    clean_text = text.strip()
    if not clean_text or len(clean_text) > 500:
        raise ValueError("invalid reminder text")
    try:
        local_due = datetime.strptime(
            "{} {}".format(local_date, local_time), "%Y-%m-%d %H:%M"
        )
    except ValueError as error:
        raise ValueError("invalid reminder time") from error
    # TODO: reject local times skipped by a daylight-saving transition.
    due_at = local_due.replace(tzinfo=ZoneInfo(user.timezone)).astimezone(timezone.utc)
    if due_at <= now.astimezone(timezone.utc):
        raise ValueError("reminder must be in the future")
    return Reminder(
        id=uuid4().hex[:8],
        owner_id=user.telegram_id,
        chat_id=user.chat_id,
        text=clean_text,
        due_at=due_at,
        created_at=now.astimezone(timezone.utc),
    )
