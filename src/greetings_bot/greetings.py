from greetings_bot.telegram import TelegramUser
from greetings_bot.users import User


def format_greeting(user: TelegramUser) -> str:
    name = user.first_name.strip()
    if not name:
        return "Hello!"
    return "Hello, {}!".format(name)


def format_scheduled_greeting(user: User) -> str:
    return "Good day, {}!".format(user.first_name)
