import logging
from typing import Optional

from greetings_bot.commands import parse_command
from greetings_bot.greetings import format_greeting
from greetings_bot.preferences import set_greeting_time
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


class Application:
    def __init__(self, users: Optional[UserRepository] = None) -> None:
        self.users = users if users is not None else InMemoryUserRepository()

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
                "Send /start for a greeting or /register to register.",
            )
        if command.name == "me":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return Reply(
                    update.message.chat_id,
                    "You are not registered. Send /register first.",
                )
            return Reply(update.message.chat_id, format_profile(user))
        if command.name == "time":
            user = self.users.get(update.message.sender.id)
            if user is None:
                return Reply(
                    update.message.chat_id,
                    "You are not registered. Send /register first.",
                )
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
    update: Update, users: Optional[UserRepository] = None
) -> Optional[Reply]:
    return Application(users).handle(update)
