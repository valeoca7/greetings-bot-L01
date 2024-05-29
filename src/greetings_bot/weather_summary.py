import logging
from datetime import datetime
from typing import Iterable, List, Optional

from greetings_bot.telegram import Reply
from greetings_bot.observability import log_event
from greetings_bot.timezones import user_local_time
from greetings_bot.users import User
from greetings_bot.weather import WeatherProvider, WeatherProviderError
from greetings_bot.weather_format import format_daily_forecast

LOGGER = logging.getLogger(__name__)


def add_weather_summaries(
    replies: Iterable[Reply],
    users: Iterable[User],
    current_time: datetime,
    provider: Optional[WeatherProvider],
) -> List[Reply]:
    replies = list(replies)
    if provider is None:
        return replies
    users_by_chat = {user.chat_id: user for user in users}
    result = []
    for reply in replies:
        user = users_by_chat.get(reply.chat_id)
        if (
            user is None
            or not user.weather_summary
            or user.digest_mode != "daily"
            or user.weather_location is None
        ):
            result.append(reply)
            continue
        forecast_date = user_local_time(user, current_time).date()
        try:
            forecast = provider.daily_forecast(
                user.weather_location, forecast_date
            )
        except WeatherProviderError:
            log_event(
                LOGGER,
                "weather_summary_failed",
                logging.WARNING,
                user_id=user.telegram_id,
                forecast_date=forecast_date.isoformat(),
            )
            result.append(reply)
            continue
        weather = format_daily_forecast(
            user.weather_location, forecast, user.weather_units
        )
        result.append(Reply(reply.chat_id, "{}\n\n{}".format(reply.text, weather)))
    return result
