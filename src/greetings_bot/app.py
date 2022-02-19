from typing import Optional

from greetings_bot.telegram import Update


def handle_update(update: Update) -> Optional[str]:
    if update.message is None:
        return None
    if update.message.text != "/start":
        return None
    return "Hello!"
