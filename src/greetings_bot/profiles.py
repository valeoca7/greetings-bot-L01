from greetings_bot.users import User


def format_profile(user: User) -> str:
    status = "on" if user.enabled else "off"
    return "Name: {}\nTelegram ID: {}\nLanguage: {}\nGreetings: {}".format(
        user.first_name,
        user.telegram_id,
        user.locale,
        status,
    )
