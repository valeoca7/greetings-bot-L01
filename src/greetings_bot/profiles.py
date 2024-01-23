from greetings_bot.users import User


def format_profile(user: User) -> str:
    status = "on" if user.enabled else "off"
    quiet_hours = (
        "off"
        if user.quiet_start is None
        else "{}-{}".format(user.quiet_start, user.quiet_end)
    )
    return (
        "Name: {}\nTelegram ID: {}\nLanguage: {}\nGreeting time: {}\n"
        "Greeting days: {}\nQuiet hours: {}\nDaily digest: {}\n"
        "Timezone: {}\nGreetings: {}"
    ).format(
        user.first_name,
        user.telegram_id,
        user.locale,
        user.greeting_time,
        ", ".join(user.greeting_days),
        quiet_hours,
        user.digest_mode,
        user.timezone,
        status,
    )
