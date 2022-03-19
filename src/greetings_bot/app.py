from typing import Optional

from greetings_bot.commands import parse_command
from greetings_bot.greetings import format_greeting
from greetings_bot.telegram import Update
from greetings_bot.users import InMemoryUserRepository, User


def handle_update(
    update: Update, users: Optional[InMemoryUserRepository] = None
) -> Optional[str]:
    if update.message is None:
        return None
    command = parse_command(update.message.text)
    if command is None:
        return None
    if command.name == "help":
        return "Send /start to get a greeting."
    if command.name == "start":
        if users is not None:
            users.save(
                User(
                    telegram_id=update.message.sender.id,
                    chat_id=update.message.chat_id,
                    first_name=update.message.sender.first_name,
                )
            )
        return format_greeting(update.message.sender)
    return "I don't know that command. Try /help."
