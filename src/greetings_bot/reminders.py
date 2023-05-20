from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta, timezone
from typing import Iterable, Literal, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from greetings_bot.users import User


ReminderStatus = Literal["pending", "sent", "cancelled"]
Recurrence = Literal["daily", "weekly"]
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


@dataclass(frozen=True)
class Reminder:
    id: str
    owner_id: int
    chat_id: int
    text: str
    due_at: datetime
    created_at: datetime
    status: ReminderStatus = "pending"
    recurrence: Optional[Recurrence] = None
    timezone: str = "UTC"


def mark_sent(reminder: Reminder) -> Reminder:
    return replace(reminder, status="sent")


def next_occurrence(reminder: Reminder) -> datetime:
    if reminder.recurrence not in ("daily", "weekly"):
        raise ValueError("reminder does not recur")
    zone = ZoneInfo(reminder.timezone)
    local_due = reminder.due_at.astimezone(zone).replace(tzinfo=None)
    interval = timedelta(days=1 if reminder.recurrence == "daily" else 7)
    candidate = local_due + interval
    while True:
        try:
            return local_to_utc(candidate, reminder.timezone)
        except ValueError:
            candidate += interval


def complete_reminder(reminder: Reminder) -> Reminder:
    if reminder.recurrence is None:
        return mark_sent(reminder)
    return replace(reminder, due_at=next_occurrence(reminder), status="pending")


def local_to_utc(local_due: datetime, timezone_name: str) -> datetime:
    zone = ZoneInfo(timezone_name)
    aware = local_due.replace(tzinfo=zone)
    utc_due = aware.astimezone(timezone.utc)
    if utc_due.astimezone(zone).replace(tzinfo=None) != local_due:
        raise ValueError("local time does not exist")
    return utc_due


def parse_clock_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as error:
        raise ValueError("invalid reminder time") from error


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
    due_at = local_to_utc(local_due, user.timezone)
    if due_at <= now.astimezone(timezone.utc):
        raise ValueError("reminder must be in the future")
    return Reminder(
        id=uuid4().hex[:8],
        owner_id=user.telegram_id,
        chat_id=user.chat_id,
        text=clean_text,
        due_at=due_at,
        created_at=now.astimezone(timezone.utc),
        timezone=user.timezone,
    )


def create_daily_reminder(
    user: User, local_time: str, text: str, now: datetime
) -> Reminder:
    clean_text = text.strip()
    if not clean_text or len(clean_text) > 500:
        raise ValueError("invalid reminder text")
    parsed_time = parse_clock_time(local_time)
    zone = ZoneInfo(user.timezone)
    local_now = now.astimezone(zone)
    local_due = datetime.combine(local_now.date(), parsed_time)
    if local_due <= local_now.replace(tzinfo=None):
        local_due += timedelta(days=1)
    due_at = local_to_utc(local_due, user.timezone)
    return Reminder(
        id=uuid4().hex[:8],
        owner_id=user.telegram_id,
        chat_id=user.chat_id,
        text=clean_text,
        due_at=due_at,
        created_at=now.astimezone(timezone.utc),
        recurrence="daily",
        timezone=user.timezone,
    )


def create_weekly_reminder(
    user: User,
    weekday: str,
    local_time: str,
    text: str,
    now: datetime,
) -> Reminder:
    clean_text = text.strip()
    if not clean_text or len(clean_text) > 500:
        raise ValueError("invalid reminder text")
    try:
        target_weekday = WEEKDAYS[weekday.lower()]
        parsed_time = parse_clock_time(local_time)
    except (KeyError, ValueError) as error:
        raise ValueError("invalid weekly reminder") from error
    zone = ZoneInfo(user.timezone)
    local_now = now.astimezone(zone)
    days_ahead = (target_weekday - local_now.weekday()) % 7
    local_due = datetime.combine(
        local_now.date() + timedelta(days=days_ahead), parsed_time
    )
    if local_due <= local_now.replace(tzinfo=None):
        local_due += timedelta(days=7)
    return Reminder(
        id=uuid4().hex[:8],
        owner_id=user.telegram_id,
        chat_id=user.chat_id,
        text=clean_text,
        due_at=local_to_utc(local_due, user.timezone),
        created_at=now.astimezone(timezone.utc),
        recurrence="weekly",
        timezone=user.timezone,
    )


def format_reminder_list(
    reminders: Iterable[Reminder], timezone_name: str
) -> str:
    zone = ZoneInfo(timezone_name)
    lines = []
    for reminder in reminders:
        state = reminder.status
        if reminder.recurrence:
            state = "{}, {}".format(state, reminder.recurrence)
        lines.append(
            "{}: {} {} ({})".format(
                reminder.id,
                reminder.due_at.astimezone(zone).strftime("%Y-%m-%d %H:%M"),
                reminder.text[:50],
                state,
            )
        )
    return "\n".join(lines)
