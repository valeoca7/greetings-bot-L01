import logging
from typing import Optional

from greetings_bot.clock import Clock, SystemClock
from greetings_bot.commands import parse_command
from greetings_bot.greetings import format_greeting
from greetings_bot.note_store import InMemoryNoteRepository, NoteRepository
from greetings_bot.notes import create_note, format_note_list
from greetings_bot.reminder_store import (
    InMemoryReminderRepository,
    ReminderRepository,
)
from greetings_bot.reminders import (
    WEEKDAYS,
    cancel_reminder,
    create_daily_reminder,
    create_reminder,
    create_weekly_reminder,
    edit_reminder_text,
    format_reminder,
    format_reminder_list,
    pause_reminder,
    parse_snooze_duration,
    resume_reminder,
    snooze_reminder,
)
from greetings_bot.preferences import (
    clear_quiet_hours,
    set_first_name,
    set_greeting_time,
    set_quiet_hours,
    set_timezone,
)
from greetings_bot.profiles import format_profile
from greetings_bot.telegram import Reply, Update
from greetings_bot.users import (
    InMemoryUserRepository,
    User,
    UserRepository,
    normalize_first_name,
    normalize_locale,
)


LOGGER = logging.getLogger(__name__)


def registration_required(chat_id: int) -> Reply:
    return Reply(chat_id, "You are not registered. Send /register first.")


class Application:
    def __init__(
        self,
        users: Optional[UserRepository] = None,
        notes: Optional[NoteRepository] = None,
        reminders: Optional[ReminderRepository] = None,
        clock: Optional[Clock] = None,
    ) -> None:
        self.users = users if users is not None else InMemoryUserRepository()
        self.notes = notes if notes is not None else InMemoryNoteRepository()
        self.reminders = (
            reminders if reminders is not None else InMemoryReminderRepository()
        )
        self.clock = clock if clock is not None else SystemClock()

    def handle(self, update: Update) -> Optional[Reply]:
        if update.message is None:
            return None
        command = parse_command(update.message.text)
        if command is None:
            return None
        LOGGER.info(
            "handling %s command from user %s",
            command.name,
            update.message.sender.id,
        )
        if command.name == "help":
            return Reply(
                update.message.chat_id,
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
        if command.name == "note" and command.arguments[:1] == ("add",):
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            try:
                note = create_note(user.telegram_id, " ".join(command.arguments[1:]))
            except ValueError as error:
                if "too long" in str(error):
                    return Reply(
                        update.message.chat_id,
                        "Note text must be 500 characters or shorter.",
                    )
                return Reply(update.message.chat_id, "Use /note add <text>.")
            self.notes.save(note)
            return Reply(
                update.message.chat_id,
                "Saved note {}.".format(note.id),
            )
        if command.name == "note" and command.arguments[:1] == ("delete",):
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            if len(command.arguments) != 2:
                return Reply(update.message.chat_id, "Use /note delete <id>.")
            if not self.notes.delete(user.telegram_id, command.arguments[1]):
                return Reply(update.message.chat_id, "Note not found.")
            return Reply(update.message.chat_id, "Note deleted.")
        if command.name == "note" and len(command.arguments) == 1:
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            note = self.notes.get(user.telegram_id, command.arguments[0])
            if note is None:
                return Reply(update.message.chat_id, "Note not found.")
            return Reply(update.message.chat_id, note.text)
        if command.name == "note":
            return Reply(
                update.message.chat_id,
                "Use /note add <text>, /note <id>, or /note delete <id>.",
            )
        if command.name == "notes":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            notes = self.notes.all_for(user.telegram_id)
            if not notes:
                return Reply(update.message.chat_id, "You have no notes.")
            return Reply(update.message.chat_id, format_note_list(notes))
        if command.name == "remind":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            if command.arguments[:2] == ("every", "day") and len(command.arguments) >= 4:
                try:
                    reminder = create_daily_reminder(
                        user,
                        command.arguments[2],
                        " ".join(command.arguments[3:]),
                        self.clock.now(),
                    )
                except ValueError:
                    return Reply(
                        update.message.chat_id,
                        "Use /remind every day HH:MM <text>.",
                    )
                self.reminders.save(reminder)
                return Reply(
                    update.message.chat_id,
                    "Daily reminder {} created.".format(reminder.id),
                )
            if (
                len(command.arguments) >= 4
                and command.arguments[:1] == ("every",)
                and command.arguments[1].lower() in WEEKDAYS
            ):
                try:
                    reminder = create_weekly_reminder(
                        user,
                        command.arguments[1],
                        command.arguments[2],
                        " ".join(command.arguments[3:]),
                        self.clock.now(),
                    )
                except ValueError:
                    return Reply(
                        update.message.chat_id,
                        "Use /remind every <weekday> HH:MM <text>.",
                    )
                self.reminders.save(reminder)
                return Reply(
                    update.message.chat_id,
                    "Weekly reminder {} created.".format(reminder.id),
                )
            if len(command.arguments) < 3:
                return Reply(
                    update.message.chat_id,
                    "Use /remind YYYY-MM-DD HH:MM <text>.",
                )
            try:
                reminder = create_reminder(
                    user,
                    command.arguments[0],
                    command.arguments[1],
                    " ".join(command.arguments[2:]),
                    self.clock.now(),
                )
            except ValueError:
                return Reply(
                    update.message.chat_id,
                    "Use a future local time: /remind YYYY-MM-DD HH:MM <text>.",
                )
            self.reminders.save(reminder)
            return Reply(
                update.message.chat_id,
                "Reminder {} set for {} {}.".format(
                    reminder.id, command.arguments[0], command.arguments[1]
                ),
            )
        if command.name == "reminders":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            reminders = self.reminders.all_for(user.telegram_id)
            if not reminders:
                return Reply(update.message.chat_id, "You have no reminders.")
            return Reply(
                update.message.chat_id,
                format_reminder_list(reminders, user.timezone),
            )
        if (
            command.name == "reminder"
            and len(command.arguments) == 2
            and command.arguments[0] in ("pause", "resume")
        ):
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            reminder = self.reminders.get(user.telegram_id, command.arguments[1])
            if reminder is None:
                return Reply(update.message.chat_id, "Reminder not found.")
            transition = (
                pause_reminder
                if command.arguments[0] == "pause"
                else resume_reminder
            )
            try:
                reminder = transition(reminder)
            except ValueError:
                return Reply(
                    update.message.chat_id,
                    "Reminder is already {}.".format(reminder.status),
                )
            self.reminders.save(reminder)
            confirmation = (
                "paused" if command.arguments[0] == "pause" else "resumed"
            )
            return Reply(
                update.message.chat_id,
                "Reminder {}.".format(confirmation),
            )
        if (
            command.name == "reminder"
            and len(command.arguments) == 2
            and command.arguments[0] == "cancel"
        ):
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            reminder = self.reminders.get(user.telegram_id, command.arguments[1])
            if reminder is None:
                return Reply(update.message.chat_id, "Reminder not found.")
            try:
                reminder = cancel_reminder(reminder)
            except ValueError:
                return Reply(update.message.chat_id, "Reminder is already complete.")
            self.reminders.save(reminder)
            return Reply(update.message.chat_id, "Reminder cancelled.")
        if (
            command.name == "reminder"
            and len(command.arguments) == 3
            and command.arguments[0] == "snooze"
        ):
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            reminder = self.reminders.get(user.telegram_id, command.arguments[1])
            if reminder is None:
                return Reply(update.message.chat_id, "Reminder not found.")
            try:
                duration = parse_snooze_duration(command.arguments[2])
                reminder = snooze_reminder(
                    reminder, duration, self.clock.now()
                )
            except ValueError:
                return Reply(
                    update.message.chat_id,
                    "Use /reminder snooze <id> <minutes|hours|days>, for example 30m.",
                )
            self.reminders.save(reminder)
            return Reply(
                update.message.chat_id,
                "Reminder snoozed until {} UTC.".format(
                    reminder.due_at.strftime("%Y-%m-%d %H:%M")
                ),
            )
        if command.name == "reminder" and command.arguments[:1] == ("edit",):
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            if len(command.arguments) < 3:
                return Reply(
                    update.message.chat_id,
                    "Use /reminder edit <id> <text>.",
                )
            reminder = self.reminders.get(user.telegram_id, command.arguments[1])
            if reminder is None:
                return Reply(update.message.chat_id, "Reminder not found.")
            try:
                reminder = edit_reminder_text(
                    reminder, " ".join(command.arguments[2:])
                )
            except ValueError:
                return Reply(update.message.chat_id, "Reminder cannot be edited.")
            self.reminders.save(reminder)
            return Reply(update.message.chat_id, "Reminder updated.")
        if command.name == "reminder" and len(command.arguments) == 1:
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            reminder = self.reminders.get(user.telegram_id, command.arguments[0])
            if reminder is None:
                return Reply(update.message.chat_id, "Reminder not found.")
            return Reply(
                update.message.chat_id,
                format_reminder(reminder, user.timezone),
            )
        if command.name == "reminder":
            return Reply(
                update.message.chat_id,
                "Use /reminder <id> or /reminder <edit|pause|resume|cancel|snooze> ...",
            )
        if command.name == "me":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            return Reply(update.message.chat_id, format_profile(user))
        if command.name == "time":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            if command.arguments:
                try:
                    user = set_greeting_time(user, command.arguments[0])
                except ValueError:
                    return Reply(
                        update.message.chat_id,
                        "Use time in HH:MM format, for example 08:30.",
                    )
                self.users.save(user)
                return Reply(
                    update.message.chat_id,
                    "Greeting time changed to {}.".format(user.greeting_time),
                )
            return Reply(
                update.message.chat_id,
                "Your greeting time is {}.".format(user.greeting_time),
            )
        if command.name == "timezone":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            if command.arguments:
                try:
                    user = set_timezone(user, command.arguments[0])
                except ValueError:
                    return Reply(
                        update.message.chat_id,
                        "Use an IANA timezone such as America/Vancouver.",
                    )
                self.users.save(user)
                return Reply(
                    update.message.chat_id,
                    "Timezone changed to {}.".format(user.timezone),
                )
            return Reply(
                update.message.chat_id,
                "Your timezone is {}.".format(user.timezone),
            )
        if command.name == "quiet":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            if len(command.arguments) == 2:
                try:
                    user = set_quiet_hours(user, *command.arguments)
                except ValueError:
                    return Reply(update.message.chat_id, "Use /quiet HH:MM HH:MM.")
                self.users.save(user)
                return Reply(
                    update.message.chat_id,
                    "Quiet hours changed to {}-{}.".format(user.quiet_start, user.quiet_end),
                )
            if command.arguments == ("off",):
                self.users.save(clear_quiet_hours(user))
                return Reply(update.message.chat_id, "Quiet hours turned off.")
            if user.quiet_start is None:
                return Reply(update.message.chat_id, "Quiet hours are off.")
            return Reply(
                update.message.chat_id,
                "Quiet hours are {}-{}.".format(user.quiet_start, user.quiet_end),
            )
        if command.name == "name":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            if command.arguments:
                try:
                    user = set_first_name(user, " ".join(command.arguments))
                except ValueError:
                    return Reply(
                        update.message.chat_id,
                        "Greeting name must be 40 characters or shorter.",
                    )
                self.users.save(user)
                return Reply(
                    update.message.chat_id,
                    "Greeting name changed to {}.".format(user.first_name),
                )
            return Reply(
                update.message.chat_id,
                "Your greeting name is {}.".format(user.first_name),
            )
        if command.name in ("start", "register"):
            existing_user = self.users.get(update.message.sender.id)
            if command.name == "register" and existing_user is not None:
                return Reply(
                    update.message.chat_id,
                    "You are already registered, {}.".format(
                        existing_user.first_name
                    ),
                )
            first_name = normalize_first_name(update.message.sender.first_name)
            self.users.save(
                User(
                    telegram_id=update.message.sender.id,
                    chat_id=update.message.chat_id,
                    first_name=first_name,
                    locale=normalize_locale(update.message.sender.language_code),
                )
            )
            if command.name == "register":
                return Reply(
                    update.message.chat_id,
                    "Thanks, {}. You are registered.".format(
                        first_name
                    ),
                )
            return Reply(
                update.message.chat_id,
                format_greeting(update.message.sender),
            )
        return Reply(update.message.chat_id, "I don't know that command. Try /help.")


def handle_update(
    update: Update,
    users: Optional[UserRepository] = None,
    notes: Optional[NoteRepository] = None,
    reminders: Optional[ReminderRepository] = None,
    clock: Optional[Clock] = None,
) -> Optional[Reply]:
    return Application(users, notes, reminders, clock).handle(update)
