from typing import Optional

from greetings_bot.commands import parse_command
from greetings_bot.greetings import format_greeting
from greetings_bot.telegram import Update


def handle_update(update: Update) -> Optional[str]:
    if update.message is None:
        return None
    command = parse_command(update.message.text)
    if command is None:
        return None
    if command.name == "help":
        return "Send /start to get a greeting."
    if command.name != "start":
        return None
    return format_greeting(update.message.sender)
