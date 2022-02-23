from greetings_bot.telegram import TelegramUser


def format_greeting(user: TelegramUser) -> str:
    name = user.first_name.strip()
    if not name:
        return "Hello!"
    return "Hello, {}!".format(name)
