from greetings_bot.users import User


def format_profile(user: User) -> str:
    status = "on" if user.enabled else "off"
    return (
        "Name: {}\nTelegram ID: {}\nLanguage: {}\nGreeting time: {}\n"
        "Greeting days: {}\nDaily digest: {}\nTimezone: {}\nGreetings: {}"
    ).format(
        user.first_name,
        user.telegram_id,
        user.locale,
        user.greeting_time,
        ", ".join(user.greeting_days),
        user.digest_mode,
        user.timezone,
        status,
    )
