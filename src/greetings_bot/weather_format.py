from greetings_bot.weather import DailyForecast, WeatherLocation


def celsius_to_fahrenheit(value: float) -> float:
    return value * 9 / 5 + 32


def format_daily_forecast(
    location: WeatherLocation,
    forecast: DailyForecast,
    units: str = "metric",
) -> str:
    low = forecast.low_celsius
    high = forecast.high_celsius
    symbol = "°C"
    if units == "imperial":
        low = celsius_to_fahrenheit(low)
        high = celsius_to_fahrenheit(high)
        symbol = "°F"
    elif units != "metric":
        raise ValueError("unknown weather units")
    return (
        "{}: {}, {:.0f}-{:.0f}{}. Precipitation chance: {}%."
    ).format(
        location.name,
        forecast.condition,
        low,
        high,
        symbol,
        forecast.precipitation_percent,
    )
