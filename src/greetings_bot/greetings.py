from typing import Optional

from greetings_bot.messages import MessageCatalog
from greetings_bot.telegram import TelegramUser
from greetings_bot.users import User


def format_greeting(
    user: TelegramUser,
    messages: Optional[MessageCatalog] = None,
    locale: str = "en",
) -> str:
    catalog = messages if messages is not None else MessageCatalog()
    name = user.first_name.strip()
    if not name:
        return catalog.text("greeting_anonymous", locale)
    return catalog.text("greeting", locale, name=name)


def format_scheduled_greeting(
    user: User, messages: Optional[MessageCatalog] = None
) -> str:
    catalog = messages if messages is not None else MessageCatalog()
    return catalog.text(
        "scheduled_greeting", user.locale, name=user.first_name
    )
