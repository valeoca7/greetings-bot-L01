from datetime import datetime
from typing import Optional

from greetings_bot.greeting_templates import (
    GreetingTemplateCatalog,
    GreetingTemplateRenderer,
)
from greetings_bot.messages import MessageCatalog
from greetings_bot.telegram import TelegramUser
from greetings_bot.timezones import user_local_time
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
    user: User,
    current_time: Optional[datetime] = None,
    templates: Optional[GreetingTemplateCatalog] = None,
    renderer: Optional[GreetingTemplateRenderer] = None,
) -> str:
    catalog = templates if templates is not None else GreetingTemplateCatalog()
    template = catalog.get(user.greeting_template_category, user.locale)
    values = {"name": user.first_name}
    if current_time is not None:
        local_time = user_local_time(user, current_time)
        values.update(
            weekday=local_time.strftime("%A"),
            date=local_time.date().isoformat(),
        )
    template_renderer = renderer or GreetingTemplateRenderer()
    return template_renderer.render(
        template,
        values,
    )
