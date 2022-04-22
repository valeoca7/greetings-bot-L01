import logging
from typing import Optional

from greetings_bot.commands import parse_command
from greetings_bot.greetings import format_greeting
from greetings_bot.telegram import Reply, Update
from greetings_bot.users import InMemoryUserRepository, User, UserRepository


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
            return Reply(update.message.chat_id, "Send /start to get a greeting.")
        if command.name == "start":
            self.users.save(
                User(
                    telegram_id=update.message.sender.id,
                    chat_id=update.message.chat_id,
                    first_name=update.message.sender.first_name,
                )
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
