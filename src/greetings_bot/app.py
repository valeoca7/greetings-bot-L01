import logging
from typing import Optional

from greetings_bot.commands import parse_command
from greetings_bot.greetings import format_greeting
from greetings_bot.note_store import InMemoryNoteRepository, NoteRepository
from greetings_bot.notes import create_note, format_note_list
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
    ) -> None:
        self.users = users if users is not None else InMemoryUserRepository()
        self.notes = notes if notes is not None else InMemoryNoteRepository()

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
                "/name [name] - show or change greeting name",
            )
        if command.name == "note" and command.arguments[:1] == ("add",):
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            try:
                note = create_note(user.telegram_id, " ".join(command.arguments[1:]))
            except ValueError:
                return Reply(update.message.chat_id, "Use /note add <text>.")
            self.notes.save(note)
            return Reply(
                update.message.chat_id,
                "Saved note {}.".format(note.id),
            )
        if command.name == "notes":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return registration_required(update.message.chat_id)
            notes = self.notes.all_for(user.telegram_id)
            if not notes:
                return Reply(update.message.chat_id, "You have no notes.")
            return Reply(update.message.chat_id, format_note_list(notes))
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
) -> Optional[Reply]:
    return Application(users, notes).handle(update)
