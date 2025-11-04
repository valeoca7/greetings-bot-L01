import unittest
from datetime import datetime, timezone

from greetings_bot.app import Application, handle_update
from greetings_bot.clock import FixedClock
from greetings_bot.information import InformationProviderError
from greetings_bot.information_quota import (
    InformationQuotaError,
    InMemoryInformationQuota,
)
from greetings_bot.messages import MessageCatalog
from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.reminders import Reminder
from greetings_bot.telegram import Message, Reply, TelegramUser, Update
from greetings_bot.users import InMemoryUserRepository, User
from greetings_bot.weather import DailyForecast, WeatherLocation, WeatherProviderError


class FakeReminderScheduler:
    def __init__(self):
        self.created = []
        self.deleted = []
        self.updated = []

    def create(self, reminder):
        self.created.append(reminder)

    def delete(self, reminder):
        self.deleted.append(reminder)

    def update(self, reminder):
        self.updated.append(reminder)


class FakeWeatherProvider:
    def __init__(self, forecast=None, error=None):
        self.forecast = forecast
        self.error = error

    def daily_forecast(self, location, forecast_date):
        self.location = location
        self.forecast_date = forecast_date
        if self.error:
            raise self.error
        return self.forecast


class FakeInformationService:
    def __init__(self, answer="A useful fact.", error=None):
        self.response = answer
        self.error = error

    def answer(self, request):
        self.request = request
        if self.error:
            raise self.error
        return self.response


def text_update(text, language_code=None):
    sender = TelegramUser(
        id=42,
        first_name="Mira",
        language_code=language_code,
    )
    message = Message(id=7, chat_id=42, sender=sender, text=text)
    return Update(id=1001, message=message)


class AppTest(unittest.TestCase):
    def test_information_requests_are_disabled_by_default(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/ask joke"), users)

        self.assertEqual(reply.text, "Information requests are not enabled.")

    def test_localizes_disabled_information_requests(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register", "uk"), users)

        reply = handle_update(text_update("/ask joke"), users)

        self.assertEqual(reply.text, "Інформаційні запити не увімкнено.")

    def test_handles_enabled_information_request(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        service = FakeInformationService("Ada wrote the first algorithm.")
        app = Application(
            users,
            information_service=service,
            information_enabled=True,
        )

        reply = app.handle(text_update("/ask person Ada Lovelace"))

        self.assertEqual(reply.text, "Ada wrote the first algorithm.")
        self.assertEqual(service.request.kind, "person")
        self.assertEqual(service.request.query, "Ada Lovelace")

    def test_rejects_invalid_information_request(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        app = Application(
            users,
            information_service=FakeInformationService(),
            information_enabled=True,
        )

        reply = app.handle(text_update("/ask person"))

        self.assertEqual(
            reply.text,
            "Use /ask joke, /ask fact, /ask person <name>, /ask place <name>, "
            "or /ask advice <topic>.",
        )

    def test_handles_an_advice_request(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        service = FakeInformationService("Try a consistent bedtime.")
        app = Application(
            users,
            information_service=service,
            information_enabled=True,
        )

        reply = app.handle(text_update("/ask advice improve sleep"))

        self.assertEqual(reply.text, "Try a consistent bedtime.")
        self.assertEqual(service.request.kind, "advice")
        self.assertEqual(service.request.query, "improve sleep")

    def test_handles_information_provider_failure(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        service = FakeInformationService(
            error=InformationProviderError("down")
        )
        app = Application(
            users,
            information_service=service,
            information_enabled=True,
        )

        reply = app.handle(text_update("/ask fact"))

        self.assertEqual(reply.text, "Information service is temporarily unavailable.")

    def test_stops_information_requests_at_the_weekly_limit(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        service = FakeInformationService()
        app = Application(
            users,
            clock=FixedClock(
                datetime(2024, 10, 22, 20, 0, tzinfo=timezone.utc)
            ),
            information_service=service,
            information_enabled=True,
            information_quota=InMemoryInformationQuota(),
            information_weekly_limit=1,
        )

        first = app.handle(text_update("/ask fact"))
        denied = app.handle(text_update("/ask joke"))

        self.assertEqual(first.text, "A useful fact.")
        self.assertEqual(
            denied.text,
            "Weekly information limit reached. It resets on 2024-10-28 UTC.",
        )
        self.assertEqual(service.request.kind, "fact")

    def test_keeps_failed_provider_attempts_in_the_quota(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        app = Application(
            users,
            clock=FixedClock(
                datetime(2024, 10, 22, 20, 0, tzinfo=timezone.utc)
            ),
            information_service=FakeInformationService(
                error=InformationProviderError("timed out")
            ),
            information_enabled=True,
            information_quota=InMemoryInformationQuota(),
            information_weekly_limit=1,
        )

        failed = app.handle(text_update("/ask fact"))
        denied = app.handle(text_update("/ask joke"))

        self.assertEqual(
            failed.text, "Information service is temporarily unavailable."
        )
        self.assertIn("Weekly information limit reached", denied.text)

    def test_does_not_call_the_provider_when_quota_storage_fails(self):
        class BrokenQuota:
            def consume(self, telegram_id, current_time, limit):
                raise InformationQuotaError("quota unavailable")

        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        service = FakeInformationService()
        app = Application(
            users,
            information_service=service,
            information_enabled=True,
            information_quota=BrokenQuota(),
        )

        reply = app.handle(text_update("/ask fact"))

        self.assertEqual(
            reply.text, "Information service is temporarily unavailable."
        )
        self.assertFalse(hasattr(service, "request"))

    def test_does_not_charge_invalid_information_commands(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        app = Application(
            users,
            information_service=FakeInformationService(),
            information_enabled=True,
            information_quota=InMemoryInformationQuota(),
            information_weekly_limit=1,
        )

        invalid = app.handle(text_update("/ask person"))
        accepted = app.handle(text_update("/ask fact"))

        self.assertIn("Use /ask joke", invalid.text)
        self.assertEqual(accepted.text, "A useful fact.")

    def test_application_keeps_its_user_repository(self):
        users = InMemoryUserRepository()
        application = Application(users)

        application.handle(text_update("/start"))

        self.assertIs(application.users, users)
        self.assertEqual(application.users.count(), 1)

    def test_application_keeps_its_note_repository(self):
        notes = InMemoryNoteRepository()

        application = Application(notes=notes)

        self.assertIs(application.notes, notes)

    def test_application_keeps_its_reminder_repository(self):
        reminders = InMemoryReminderRepository()

        application = Application(reminders=reminders)

        self.assertIs(application.reminders, reminders)

    def test_application_keeps_its_weather_provider(self):
        provider = object()

        application = Application(weather_provider=provider)

        self.assertIs(application.weather_provider, provider)

    def test_handles_start_command(self):
        reply = handle_update(text_update("/start"))

        self.assertEqual(reply, Reply(chat_id=42, text="Hello, Mira!"))

    def test_handles_help_command(self):
        reply = handle_update(text_update("/help"))

        self.assertEqual(
            reply.text,
            "Available commands:\n"
            "/start - get a greeting\n"
            "/register - create a profile\n"
            "/me - show your profile\n"
            "/language [en|uk] - show or change language\n"
            "/style [friendly|brief|cheerful] - choose greeting style\n"
            "/preview - preview the scheduled greeting\n"
            "/time [HH:MM] - show or change greeting time\n"
            "/days [daily|weekdays|days...] - choose greeting days\n"
            "/digest [daily|off] - manage the daily digest\n"
            "/location [lat lon name|off] - manage weather location\n"
            "/weather [daily|off] - forecast or daily summary\n"
            "/ask <joke|fact|person|place|advice> - request short information\n"
            "/timezone [area/name] - show or change timezone\n"
            "/quiet [start end|off] - manage quiet hours\n"
            "/name [name] - show or change greeting name\n"
            "/note add <text> - save a note\n"
            "/notes - list saved notes\n"
            "/remind YYYY-MM-DD HH:MM <text> - set a reminder\n"
            "/remind every day HH:MM <text> - repeat daily\n"
            "/remind every <weekday> HH:MM <text> - repeat weekly\n"
            "/reminders - list reminders\n"
            "/reminder <id> - view or manage a reminder",
        )
        self.assertEqual(reply.chat_id, 42)

    def test_uses_sender_locale_for_help_before_registration(self):
        messages = MessageCatalog({"fr": {"help": "Commandes disponibles"}})

        reply = Application(messages=messages).handle(
            text_update("/help", "fr-CA")
        )

        self.assertEqual(reply.text, "Commandes disponibles")

    def test_ignores_other_messages(self):
        self.assertIsNone(handle_update(text_update("hello")))

    def test_replies_to_unknown_commands(self):
        reply = handle_update(text_update("/something"))

        self.assertEqual(reply.text, "I don't know that command. Try /help.")

    def test_registers_user_on_start(self):
        users = InMemoryUserRepository()

        handle_update(text_update("/start"), users)

        self.assertEqual(users.get(42).first_name, "Mira")
        self.assertEqual(users.get(42).chat_id, 42)

    def test_uses_telegram_language_during_registration(self):
        users = InMemoryUserRepository()

        reply = handle_update(text_update("/register", "uk"), users)

        self.assertEqual(users.get(42).locale, "uk")
        self.assertEqual(reply.text, "Дякую, Mira. Реєстрацію завершено.")

    def test_handles_register_command(self):
        users = InMemoryUserRepository()

        reply = handle_update(text_update("/register"), users)

        self.assertEqual(reply.text, "Thanks, Mira. You are registered.")
        self.assertIsNotNone(users.get(42))

    def test_localizes_registration_confirmation(self):
        messages = MessageCatalog(
            {
                "fr": {
                    "registration_complete": "Merci, {name}. Inscription terminée."
                }
            }
        )

        reply = Application(messages=messages).handle(
            text_update("/register", "fr")
        )

        self.assertEqual(reply.text, "Merci, Mira. Inscription terminée.")

    def test_does_not_duplicate_an_existing_user(self):
        users = InMemoryUserRepository()

        handle_update(text_update("/start"), users)
        handle_update(text_update("/start"), users)

        self.assertEqual(users.count(), 1)

    def test_reports_an_existing_registration(self):
        users = InMemoryUserRepository()

        handle_update(text_update("/register"), users)
        reply = handle_update(text_update("/register"), users)

        self.assertEqual(reply.text, "You are already registered, Mira.")
        self.assertEqual(users.count(), 1)

    def test_shows_current_user(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/me"), users)

        self.assertEqual(
            reply.text,
            "Name: Mira\nTelegram ID: 42\nLanguage: en\n"
            "Greeting time: 09:00\nGreeting days: mon, tue, wed, thu, fri, sat, sun\n"
            "Quiet hours: off\nDaily digest: off\nWeather location: not set\n"
            "Weather units: metric\nDaily weather: off\nTimezone: UTC\nGreetings: on",
        )

    def test_shows_and_changes_language(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        current = handle_update(text_update("/language"), users)
        changed = handle_update(text_update("/language uk"), users)
        localized = handle_update(text_update("/language"), users)

        self.assertEqual(current.text, "Your language is en.")
        self.assertEqual(changed.text, "Мову змінено на uk.")
        self.assertEqual(localized.text, "Ваша мова: uk.")
        self.assertEqual(users.get(42).locale, "uk")

    def test_rejects_an_unsupported_language(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/language fr"), users)

        self.assertEqual(reply.text, "Use /language en or /language uk.")
        self.assertEqual(users.get(42).locale, "en")

    def test_shows_and_changes_greeting_style(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        current = handle_update(text_update("/style"), users)
        changed = handle_update(text_update("/style cheerful"), users)

        self.assertEqual(current.text, "Your greeting style is friendly.")
        self.assertEqual(changed.text, "Greeting style changed to cheerful.")
        self.assertEqual(users.get(42).greeting_template_category, "cheerful")

    def test_localizes_greeting_style_feedback(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register", "uk"), users)

        reply = handle_update(text_update("/style brief"), users)

        self.assertEqual(reply.text, "Стиль привітання змінено на brief.")

    def test_rejects_an_unknown_greeting_style(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/style loud"), users)

        self.assertEqual(
            reply.text,
            "Use /style friendly, /style brief, or /style cheerful.",
        )
        self.assertEqual(users.get(42).greeting_template_category, "friendly")

    def test_previews_the_selected_greeting_style(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        handle_update(text_update("/style cheerful"), users)

        reply = handle_update(
            text_update("/preview"),
            users,
            clock=FixedClock(datetime(2025, 11, 3, 20, 0, tzinfo=timezone.utc)),
        )

        self.assertEqual(
            reply.text,
            "Preview:\nHope your day starts well, Mira!",
        )

    def test_localizes_a_greeting_preview(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register", "uk"), users)

        reply = handle_update(text_update("/preview"), users)

        self.assertEqual(
            reply.text,
            "Попередній перегляд:\nДобрий день, Mira!",
        )

    def test_reports_missing_profile(self):
        reply = handle_update(text_update("/me"), InMemoryUserRepository())

        self.assertEqual(
            reply.text,
            "You are not registered. Send /register first.",
        )

    def test_shows_greeting_time(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/time"), users)

        self.assertEqual(reply.text, "Your greeting time is 09:00.")

    def test_changes_greeting_time(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/time 18:30"), users)

        self.assertEqual(reply.text, "Greeting time changed to 18:30.")
        self.assertEqual(users.get(42).greeting_time, "18:30")

    def test_rejects_invalid_greeting_time(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/time evening"), users)

        self.assertEqual(
            reply.text,
            "Use time in HH:MM format, for example 08:30.",
        )
        self.assertEqual(users.get(42).greeting_time, "09:00")

    def test_shows_and_changes_greeting_days(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        current = handle_update(text_update("/days"), users)
        changed = handle_update(text_update("/days mon wed friday"), users)

        self.assertIn("mon, tue, wed, thu, fri, sat, sun", current.text)
        self.assertEqual(changed.text, "Greeting days changed to mon, wed, fri.")
        self.assertEqual(users.get(42).greeting_days, ("mon", "wed", "fri"))

    def test_rejects_unknown_greeting_day(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/days someday"), users)

        self.assertEqual(
            reply.text,
            "Use /days daily, /days weekdays, or /days mon wed fri.",
        )

    def test_shows_and_changes_digest_mode(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        current = handle_update(text_update("/digest"), users)
        changed = handle_update(text_update("/digest daily"), users)

        self.assertEqual(current.text, "Daily digest is off.")
        self.assertEqual(changed.text, "Daily digest is on.")
        self.assertEqual(users.get(42).digest_mode, "daily")

    def test_rejects_unknown_digest_mode(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/digest weekly"), users)

        self.assertEqual(reply.text, "Use /digest daily or /digest off.")

    def test_sets_and_shows_weather_location(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        changed = handle_update(
            text_update("/location 49.2827 -123.1207 Vancouver BC"), users
        )
        current = handle_update(text_update("/location"), users)

        self.assertEqual(changed.text, "Weather location set to Vancouver BC.")
        self.assertEqual(
            current.text,
            "Weather location is Vancouver BC (49.2827, -123.1207).",
        )

    def test_removes_weather_location(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        handle_update(text_update("/location 49 -123 Vancouver"), users)

        reply = handle_update(text_update("/location off"), users)

        self.assertEqual(reply.text, "Weather location removed.")
        self.assertIsNone(users.get(42).weather_location)

    def test_rejects_invalid_weather_location(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/location north west Home"), users)

        self.assertEqual(
            reply.text,
            "Use /location <latitude> <longitude> <name>.",
        )

    def test_changes_weather_units(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/weather units imperial"), users)

        self.assertEqual(reply.text, "Weather units changed to imperial.")
        self.assertEqual(users.get(42).weather_units, "imperial")

    def test_enables_daily_weather_summary(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        handle_update(text_update("/location 49 -123 Vancouver"), users)

        reply = handle_update(text_update("/weather daily"), users)

        self.assertEqual(reply.text, "Daily weather summary is on.")
        self.assertTrue(users.get(42).weather_summary)

    def test_daily_weather_requires_a_location(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/weather daily"), users)

        self.assertEqual(
            reply.text,
            "Set a weather location with /location first.",
        )

    def test_turns_off_daily_weather_summary(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        handle_update(text_update("/location 49 -123 Vancouver"), users)
        handle_update(text_update("/weather daily"), users)

        reply = handle_update(text_update("/weather off"), users)

        self.assertEqual(reply.text, "Daily weather summary is off.")
        self.assertFalse(users.get(42).weather_summary)

    def test_localizes_weather_preferences(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register", "uk"), users)

        location = handle_update(
            text_update("/location 50.4501 30.5234 Київ"), users
        )
        daily = handle_update(text_update("/weather daily"), users)

        self.assertEqual(location.text, "Місце для погоди змінено на Київ.")
        self.assertEqual(daily.text, "Щоденний огляд погоди увімкнено.")

    def test_location_removal_confirms_daily_weather_cleanup(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        handle_update(text_update("/location 49 -123 Vancouver"), users)
        handle_update(text_update("/weather daily"), users)

        reply = handle_update(text_update("/location off"), users)

        self.assertEqual(
            reply.text,
            "Weather location and daily summary removed.",
        )

    def test_rejects_unknown_weather_units(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/weather units kelvin"), users)

        self.assertEqual(
            reply.text,
            "Use /weather units metric or /weather units imperial.",
        )

    def test_returns_todays_weather(self):
        users = InMemoryUserRepository()
        users.save(
            User(
                42,
                42,
                "Mira",
                timezone="America/Vancouver",
                weather_location=WeatherLocation("Vancouver", 49.2, -123.1),
            )
        )
        provider = FakeWeatherProvider(
            DailyForecast(
                datetime(2024, 4, 1).date(), 3, 9, "rain", 60
            )
        )
        app = Application(
            users=users,
            clock=FixedClock(datetime(2024, 4, 2, 1, 0, tzinfo=timezone.utc)),
            weather_provider=provider,
        )

        reply = app.handle(text_update("/weather"))

        self.assertEqual(provider.forecast_date.isoformat(), "2024-04-01")
        self.assertEqual(
            reply.text,
            "Vancouver: rain, 3-9°C. Precipitation chance: 60%.",
        )

    def test_returns_weather_in_saved_imperial_units(self):
        users = InMemoryUserRepository()
        users.save(
            User(
                42,
                42,
                "Mira",
                weather_location=WeatherLocation("Vancouver", 49.2, -123.1),
                weather_units="imperial",
            )
        )
        provider = FakeWeatherProvider(
            DailyForecast(datetime(2024, 4, 15).date(), 0, 10, "clear", 5)
        )

        reply = Application(users, weather_provider=provider).handle(
            text_update("/weather")
        )

        self.assertEqual(
            reply.text,
            "Vancouver: clear, 32-50°F. Precipitation chance: 5%.",
        )

    def test_requires_a_weather_location(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = Application(users, weather_provider=FakeWeatherProvider()).handle(
            text_update("/weather")
        )

        self.assertEqual(
            reply.text,
            "Set a weather location with /location first.",
        )

    def test_handles_weather_provider_failure(self):
        users = InMemoryUserRepository()
        users.save(
            User(
                42,
                42,
                "Mira",
                weather_location=WeatherLocation("Vancouver", 49.2, -123.1),
            )
        )
        provider = FakeWeatherProvider(error=WeatherProviderError("down"))

        reply = Application(users, weather_provider=provider).handle(
            text_update("/weather")
        )

        self.assertEqual(reply.text, "Weather is temporarily unavailable.")

    def test_handles_unconfigured_weather_provider(self):
        users = InMemoryUserRepository()
        users.save(
            User(
                42,
                42,
                "Mira",
                weather_location=WeatherLocation("Vancouver", 49.2, -123.1),
            )
        )

        reply = Application(users).handle(text_update("/weather"))

        self.assertEqual(reply.text, "Weather is temporarily unavailable.")

    def test_shows_timezone(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/timezone"), users)

        self.assertEqual("Your timezone is UTC.", reply.text)

    def test_changes_timezone(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/timezone America/Vancouver"), users)

        self.assertEqual("Timezone changed to America/Vancouver.", reply.text)
        self.assertEqual("America/Vancouver", users.get(42).timezone)

    def test_rejects_unknown_timezone(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/timezone Mars/Base"), users)

        self.assertEqual("Use an IANA timezone such as America/Vancouver.", reply.text)

    def test_sets_quiet_hours(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/quiet 22:00 07:00"), users)

        self.assertEqual("Quiet hours changed to 22:00-07:00.", reply.text)

    def test_shows_disabled_quiet_hours(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/quiet"), users)

        self.assertEqual("Quiet hours are off.", reply.text)

    def test_turns_off_quiet_hours(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)
        handle_update(text_update("/quiet 22:00 07:00"), users)

        reply = handle_update(text_update("/quiet off"), users)

        self.assertEqual("Quiet hours turned off.", reply.text)
        self.assertIsNone(users.get(42).quiet_start)

    def test_rejects_incomplete_quiet_hours(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/quiet later"), users)

        self.assertEqual(
            reply.text,
            "Use /quiet HH:MM HH:MM or /quiet off.",
        )

    def test_shows_greeting_name(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/name"), users)

        self.assertEqual(reply.text, "Your greeting name is Mira.")

    def test_changes_greeting_name(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/name Mira Jane"), users)

        self.assertEqual(reply.text, "Greeting name changed to Mira Jane.")
        self.assertEqual(users.get(42).first_name, "Mira Jane")

    def test_rejects_long_greeting_name(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/name " + "x" * 41), users)

        self.assertEqual(
            reply.text,
            "Greeting name must be 40 characters or shorter.",
        )

    def test_adds_note(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)

        reply = handle_update(text_update("/note add Call the dentist"), users, notes)

        self.assertTrue(reply.text.startswith("Saved note "))
        self.assertEqual(notes.all_for(42)[0].text, "Call the dentist")

    def test_requires_registration_before_saving_note(self):
        notes = InMemoryNoteRepository()

        reply = handle_update(
            text_update("/note add Private text"),
            InMemoryUserRepository(),
            notes,
        )

        self.assertEqual(reply.text, "You are not registered. Send /register first.")
        self.assertEqual(notes.all_for(42), [])

    def test_localizes_registration_required_for_an_unregistered_sender(self):
        reply = handle_update(text_update("/notes", "uk-UA"))

        self.assertEqual(
            reply.text,
            "Ви не зареєстровані. Спочатку надішліть /register.",
        )

    def test_lists_notes(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)
        saved = handle_update(text_update("/note add Buy tea"), users, notes)
        note_id = saved.text.split()[2].rstrip(".")

        reply = handle_update(text_update("/notes"), users, notes)

        self.assertEqual(reply.text, "{}: Buy tea".format(note_id))

    def test_reports_empty_note_list(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)

        reply = handle_update(text_update("/notes"), users, notes)

        self.assertEqual(reply.text, "You have no notes.")

    def test_localizes_note_responses(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register", "uk"), users, notes)

        saved = handle_update(text_update("/note add Купити чай"), users, notes)
        empty_users_notes = InMemoryNoteRepository()
        empty = handle_update(text_update("/notes"), users, empty_users_notes)

        self.assertTrue(saved.text.startswith("Нотатку "))
        self.assertEqual(empty.text, "У вас немає нотаток.")

    def test_shows_note_by_id(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)
        saved = handle_update(text_update("/note add Buy green tea"), users, notes)
        note_id = saved.text.split()[2].rstrip(".")

        reply = handle_update(text_update("/note " + note_id), users, notes)

        self.assertEqual(reply.text, "Buy green tea")

    def test_hides_unknown_note(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/note missing"), users)

        self.assertEqual(reply.text, "Note not found.")

    def test_deletes_note(self):
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        handle_update(text_update("/register"), users, notes)
        saved = handle_update(text_update("/note add Temporary"), users, notes)
        note_id = saved.text.split()[2].rstrip(".")

        reply = handle_update(
            text_update("/note delete " + note_id), users, notes
        )

        self.assertEqual(reply.text, "Note deleted.")
        self.assertEqual(notes.all_for(42), [])

    def test_reports_unknown_note_on_delete(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/note delete missing"), users)

        self.assertEqual(reply.text, "Note not found.")

    def test_explains_note_command(self):
        reply = handle_update(text_update("/note"))

        self.assertEqual(
            reply.text,
            "Use /note add <text>, /note <id>, or /note delete <id>.",
        )

    def test_creates_one_time_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(
            text_update("/remind 2023-04-01 09:30 Call home"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 3, 17, 18, 0, tzinfo=timezone.utc)),
        )

        self.assertIn("set for 2023-04-01 09:30", reply.text)
        self.assertEqual(reminders.all_for(42)[0].text, "Call home")

    def test_localizes_reminder_creation_and_empty_list(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register", "uk"), users)

        created = handle_update(
            text_update("/remind 2023-04-01 09:30 Подзвонити додому"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 3, 17, 18, 0, tzinfo=timezone.utc)),
        )
        empty = handle_update(
            text_update("/reminders"),
            users,
            reminders=InMemoryReminderRepository(),
        )

        self.assertTrue(created.text.startswith("Нагадування "))
        self.assertIn("встановлено на 2023-04-01 09:30", created.text)
        self.assertEqual(empty.text, "У вас немає нагадувань.")

    def test_schedules_one_time_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        scheduler = FakeReminderScheduler()
        handle_update(text_update("/register"), users)

        handle_update(
            text_update("/remind 2023-09-01 09:30 Call home"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 8, 9, 18, 0, tzinfo=timezone.utc)),
            reminder_scheduler=scheduler,
        )

        self.assertEqual(scheduler.created, reminders.all_for(42))

    def test_removes_paused_schedule_and_recreates_on_resume(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        scheduler = FakeReminderScheduler()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind 2023-09-01 09:30 Call home"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 8, 10, 18, 0, tzinfo=timezone.utc)),
            reminder_scheduler=scheduler,
        )
        reminder_id = created.text.split()[1]

        handle_update(
            text_update("/reminder pause " + reminder_id),
            users,
            reminders=reminders,
            reminder_scheduler=scheduler,
        )
        handle_update(
            text_update("/reminder resume " + reminder_id),
            users,
            reminders=reminders,
            reminder_scheduler=scheduler,
        )

        self.assertEqual(len(scheduler.deleted), 1)
        self.assertEqual(len(scheduler.created), 2)

    def test_lists_reminders(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        clock = FixedClock(datetime(2023, 3, 17, 18, 0, tzinfo=timezone.utc))
        handle_update(
            text_update("/remind 2023-04-01 09:30 Call home"),
            users,
            reminders=reminders,
            clock=clock,
        )

        reply = handle_update(
            text_update("/reminders"), users, reminders=reminders
        )

        self.assertIn("2023-04-01 09:30 Call home (pending)", reply.text)

    def test_reports_empty_reminder_list(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/reminders"), users)

        self.assertEqual(reply.text, "You have no reminders.")

    def test_shows_owned_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind 2023-07-01 09:30 Call home"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 6, 15, 18, 0, tzinfo=timezone.utc)),
        )
        reminder_id = created.text.split()[1]

        reply = handle_update(
            text_update("/reminder " + reminder_id),
            users,
            reminders=reminders,
        )

        self.assertIn("Call home\nDue: 2023-07-01 09:30", reply.text)

    def test_hides_unknown_reminder(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/reminder missing"), users)

        self.assertEqual(reply.text, "Reminder not found.")

    def test_edits_reminder_text(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind 2023-07-01 09:30 Old text"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 6, 19, 18, 0, tzinfo=timezone.utc)),
        )
        reminder_id = created.text.split()[1]

        reply = handle_update(
            text_update("/reminder edit {} New text".format(reminder_id)),
            users,
            reminders=reminders,
        )

        self.assertEqual(reply.text, "Reminder updated.")
        self.assertEqual(reminders.get(42, reminder_id).text, "New text")

    def test_pauses_and_resumes_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind every day 09:30 Stretch"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 6, 20, 18, 0, tzinfo=timezone.utc)),
        )
        reminder_id = created.text.split()[2]

        paused = handle_update(
            text_update("/reminder pause " + reminder_id),
            users,
            reminders=reminders,
        )
        resumed = handle_update(
            text_update("/reminder resume " + reminder_id),
            users,
            reminders=reminders,
        )

        self.assertEqual(paused.text, "Reminder paused.")
        self.assertEqual(resumed.text, "Reminder resumed.")
        self.assertEqual(reminders.get(42, reminder_id).status, "pending")

    def test_localizes_reminder_management(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register", "uk"), users)
        handle_update(
            text_update("/remind every day 09:30 Розім'ятися"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 6, 20, 18, 0, tzinfo=timezone.utc)),
        )
        reminder_id = reminders.all_for(42)[0].id

        paused = handle_update(
            text_update("/reminder pause " + reminder_id),
            users,
            reminders=reminders,
        )
        resumed = handle_update(
            text_update("/reminder resume " + reminder_id),
            users,
            reminders=reminders,
        )

        self.assertEqual(paused.text, "Нагадування призупинено.")
        self.assertEqual(resumed.text, "Нагадування відновлено.")

    def test_cancels_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind 2023-07-01 09:30 Cancel me"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 6, 23, 18, 0, tzinfo=timezone.utc)),
        )
        reminder_id = created.text.split()[1]

        reply = handle_update(
            text_update("/reminder cancel " + reminder_id),
            users,
            reminders=reminders,
        )

        self.assertEqual(reply.text, "Reminder cancelled.")
        self.assertEqual(reminders.get(42, reminder_id).status, "cancelled")

    def test_cancellation_deletes_one_time_schedule(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        scheduler = FakeReminderScheduler()
        handle_update(text_update("/register"), users)
        created = handle_update(
            text_update("/remind 2023-09-01 09:30 Cancel me"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 8, 14, 18, 0, tzinfo=timezone.utc)),
            reminder_scheduler=scheduler,
        )
        reminder_id = created.text.split()[1]

        handle_update(
            text_update("/reminder cancel " + reminder_id),
            users,
            reminders=reminders,
            reminder_scheduler=scheduler,
        )

        self.assertEqual(len(scheduler.deleted), 1)

    def test_snoozes_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        clock = FixedClock(datetime(2023, 6, 26, 18, 0, tzinfo=timezone.utc))
        created = handle_update(
            text_update("/remind 2023-07-01 09:30 Later"),
            users,
            reminders=reminders,
            clock=clock,
        )
        reminder_id = created.text.split()[1]

        reply = handle_update(
            text_update("/reminder snooze {} 30m".format(reminder_id)),
            users,
            reminders=reminders,
            clock=clock,
        )

        self.assertEqual(
            reply.text, "Reminder snoozed until 2023-06-26 18:30 local time."
        )
        self.assertEqual(
            reminders.get(42, reminder_id).due_at,
            datetime(2023, 6, 26, 18, 30, tzinfo=timezone.utc),
        )

    def test_snooze_updates_one_time_schedule(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        scheduler = FakeReminderScheduler()
        handle_update(text_update("/register"), users)
        clock = FixedClock(datetime(2023, 8, 14, 18, 0, tzinfo=timezone.utc))
        created = handle_update(
            text_update("/remind 2023-09-01 09:30 Later"),
            users,
            reminders=reminders,
            clock=clock,
            reminder_scheduler=scheduler,
        )
        reminder_id = created.text.split()[1]

        handle_update(
            text_update("/reminder snooze {} 1h".format(reminder_id)),
            users,
            reminders=reminders,
            clock=clock,
            reminder_scheduler=scheduler,
        )

        self.assertEqual(len(scheduler.updated), 1)

    def test_explains_reminder_management_command(self):
        reply = handle_update(text_update("/reminder"))

        self.assertEqual(
            reply.text,
            "Use /reminder <id> or /reminder <edit|pause|resume|cancel|snooze> ...",
        )

    def test_cannot_manage_another_users_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)
        reminders.save(
            Reminder(
                "private1", 7, 7, "Private",
                datetime(2023, 7, 10, 18, 0, tzinfo=timezone.utc),
                datetime(2023, 7, 1, 18, 0, tzinfo=timezone.utc),
            )
        )

        reply = handle_update(
            text_update("/reminder pause private1"),
            users,
            reminders=reminders,
        )

        self.assertEqual(reply.text, "Reminder not found.")
        self.assertEqual(reminders.get(7, "private1").status, "pending")

    def test_creates_daily_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(
            text_update("/remind every day 09:00 Drink water"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 5, 8, 18, 0, tzinfo=timezone.utc)),
        )

        self.assertTrue(reply.text.startswith("Daily reminder "))
        self.assertEqual(reminders.all_for(42)[0].recurrence, "daily")

    def test_creates_weekly_reminder(self):
        users = InMemoryUserRepository()
        reminders = InMemoryReminderRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(
            text_update("/remind every monday 09:00 Plan week"),
            users,
            reminders=reminders,
            clock=FixedClock(datetime(2023, 5, 8, 18, 0, tzinfo=timezone.utc)),
        )

        self.assertTrue(reply.text.startswith("Weekly reminder "))
        self.assertEqual(reminders.all_for(42)[0].recurrence, "weekly")

    def test_rejects_long_note_text(self):
        users = InMemoryUserRepository()
        handle_update(text_update("/register"), users)

        reply = handle_update(text_update("/note add " + "x" * 501), users)

        self.assertEqual(
            reply.text,
            "Note text must be 500 characters or shorter.",
        )

    def test_logs_command_without_its_arguments(self):
        with self.assertLogs("greetings_bot.app", level="INFO") as logs:
            handle_update(text_update("/start private-text"))

        self.assertIn("start command from user 42", logs.output[0])
        self.assertNotIn("private-text", logs.output[0])

    def test_ignores_updates_without_messages(self):
        self.assertIsNone(handle_update(Update(id=1002)))


if __name__ == "__main__":
    unittest.main()
