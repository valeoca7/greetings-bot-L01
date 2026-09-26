from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta, timezone
from typing import Iterable, Literal, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from greetings_bot.messages import MessageCatalog
from greetings_bot.users import User


ReminderStatus = Literal["pending", "paused", "sent", "cancelled"]
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


def pause_reminder(reminder: Reminder) -> Reminder:
    if reminder.status != "pending":
        raise ValueError("only pending reminders can be paused")
    return replace(reminder, status="paused")


def resume_reminder(reminder: Reminder) -> Reminder:
    if reminder.status != "paused":
        raise ValueError("only paused reminders can be resumed")
    return replace(reminder, status="pending")


def edit_reminder_text(reminder: Reminder, text: str) -> Reminder:
    clean_text = text.strip()
    if not clean_text or len(clean_text) > 500:
        raise ValueError("invalid reminder text")
    if reminder.status in ("sent", "cancelled"):
        raise ValueError("completed reminder cannot be edited")
    return replace(reminder, text=clean_text)


def cancel_reminder(reminder: Reminder) -> Reminder:
    if reminder.status in ("sent", "cancelled"):
        raise ValueError("reminder is already complete")
    return replace(reminder, status="cancelled")


def parse_snooze_duration(value: str) -> timedelta:
    units = {"m": 1, "h": 60, "d": 1440}
    try:
        amount = int(value[:-1])
        minutes = amount * units[value[-1].lower()]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid snooze duration") from error
    if minutes < 1 or minutes > 7 * 24 * 60:
        raise ValueError("invalid snooze duration")
    return timedelta(minutes=minutes)


def snooze_reminder(
    reminder: Reminder, duration: timedelta, now: datetime
) -> Reminder:
    if reminder.status not in ("pending", "paused"):
        raise ValueError("completed reminder cannot be snoozed")
    return replace(
        reminder,
        due_at=now.astimezone(timezone.utc) + duration,
        status="pending",
    )


def next_occurrence(reminder: Reminder) -> datetime:
    if reminder.recurrence not in ("daily", "weekly"):
        raise ValueError("reminder does not recur")
    zone = ZoneInfo(reminder.timezone)
    local_due = reminder.due_at.astimezone(zone).replace(tzinfo=None)
    interval = timedelta(days=1 if reminder.recurrence == "daily" else 7)
    return _next_valid_local_time(
        local_due + interval, reminder.timezone, interval
    )


def _next_valid_local_time(
    candidate: datetime, timezone_name: str, interval: timedelta
) -> datetime:
    while True:
        try:
            return local_to_utc(candidate, timezone_name)
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
    due_at = _next_valid_local_time(
        local_due, user.timezone, timedelta(days=1)
    )
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
        due_at=_next_valid_local_time(
            local_due, user.timezone, timedelta(days=7)
        ),
        created_at=now.astimezone(timezone.utc),
        recurrence="weekly",
        timezone=user.timezone,
    )


def format_reminder_list(
    reminders: Iterable[Reminder],
    timezone_name: str,
    messages: Optional[MessageCatalog] = None,
    locale: str = "en",
) -> str:
    catalog = messages if messages is not None else MessageCatalog()
    zone = ZoneInfo(timezone_name)
    lines = []
    for reminder in reminders:
        state = catalog.text(
            "reminder_status_{}".format(reminder.status), locale
        )
        if reminder.recurrence:
            repeat = catalog.text(
                "reminder_repeat_{}".format(reminder.recurrence), locale
            )
            state = "{}, {}".format(state, repeat)
        lines.append(
            "{}: {} {} ({})".format(
                reminder.id,
                reminder.due_at.astimezone(zone).strftime("%Y-%m-%d %H:%M"),
                reminder.text[:50],
                state,
            )
        )
    return "\n".join(lines)


def format_reminder(
    reminder: Reminder,
    timezone_name: str,
    messages: Optional[MessageCatalog] = None,
    locale: str = "en",
) -> str:
    catalog = messages if messages is not None else MessageCatalog()
    local_due = format_due_time(reminder, timezone_name)
    repeat = catalog.text(
        "reminder_repeat_{}".format(reminder.recurrence or "once"), locale
    )
    return catalog.text(
        "reminder_details",
        locale,
        text=reminder.text,
        due_time=local_due,
        status=catalog.text(
            "reminder_status_{}".format(reminder.status), locale
        ),
        repeat=repeat,
    )


def format_due_time(reminder: Reminder, timezone_name: str) -> str:
    return reminder.due_at.astimezone(ZoneInfo(timezone_name)).strftime(
        "%Y-%m-%d %H:%M"
    )
