from typing import Optional

from greetings_bot.messages import MessageCatalog
from greetings_bot.users import User


def format_profile(
    user: User, messages: Optional[MessageCatalog] = None
) -> str:
    catalog = messages if messages is not None else MessageCatalog()
    status = catalog.text("state_on" if user.enabled else "state_off", user.locale)
    quiet_hours = (
        catalog.text("state_off", user.locale)
        if user.quiet_start is None
        else "{}-{}".format(user.quiet_start, user.quiet_end)
    )
    weather_location = (
        catalog.text("not_set", user.locale)
        if user.weather_location is None
        else user.weather_location.name
    )
    weather_summary = catalog.text(
        "state_on" if user.weather_summary else "state_off", user.locale
    )
    digest = (
        catalog.text("state_daily", user.locale)
        if user.digest_mode == "daily"
        else catalog.text("state_off", user.locale)
    )
    profile = catalog.text(
        "profile",
        user.locale,
        name=user.first_name,
        telegram_id=user.telegram_id,
        locale=user.locale,
        greeting_style=user.greeting_template_category,
        greeting_time=user.greeting_time,
        greeting_days=", ".join(user.greeting_days),
        quiet_hours=quiet_hours,
        digest=digest,
        weather_location=weather_location,
        weather_units=user.weather_units,
        weather_summary=weather_summary,
        timezone=user.timezone,
        greetings=status,
    )
    resolved_locale = catalog.resolved_locale("profile", user.locale)
    if resolved_locale != user.locale.replace("_", "-").lower():
        profile += "\n" + catalog.text(
            "profile_fallback", resolved_locale, locale=resolved_locale
        )
    return profile
