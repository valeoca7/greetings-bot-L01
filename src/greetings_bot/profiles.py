from greetings_bot.users import User


def format_profile(user: User) -> str:
    status = "on" if user.enabled else "off"
    quiet_hours = (
        "off"
        if user.quiet_start is None
        else "{}-{}".format(user.quiet_start, user.quiet_end)
    )
    weather_location = (
        "not set"
        if user.weather_location is None
        else user.weather_location.name
    )
    return (
        "Name: {}\nTelegram ID: {}\nLanguage: {}\nGreeting time: {}\n"
        "Greeting days: {}\nQuiet hours: {}\nDaily digest: {}\n"
        "Weather location: {}\nWeather units: {}\nTimezone: {}\nGreetings: {}"
    ).format(
        user.first_name,
        user.telegram_id,
        user.locale,
        user.greeting_time,
        ", ".join(user.greeting_days),
        quiet_hours,
        user.digest_mode,
        weather_location,
        user.weather_units,
        user.timezone,
        status,
    )
