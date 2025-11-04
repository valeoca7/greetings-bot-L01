from string import Formatter
from typing import Dict, Mapping, Tuple


ENGLISH_MESSAGES = {
    "registration_required": "You are not registered. Send /register first.",
    "already_registered": "You are already registered, {name}.",
    "registration_complete": "Thanks, {name}. You are registered.",
    "unknown_command": "I don't know that command. Try /help.",
    "language_current": "Your language is {locale}.",
    "language_changed": "Language changed to {locale}.",
    "language_usage": "Use /language en or /language uk.",
    "style_current": "Your greeting style is {category}.",
    "style_changed": "Greeting style changed to {category}.",
    "style_usage": "Use /style friendly, /style brief, or /style cheerful.",
    "greeting_preview": "Preview:\n{greeting}",
    "greeting_preview_usage": "Use /preview without arguments.",
    "state_on": "on",
    "state_off": "off",
    "state_daily": "daily",
    "not_set": "not set",
    "note_add_usage": "Use /note add <text>.",
    "note_too_long": "Note text must be 500 characters or shorter.",
    "note_saved": "Saved note {note_id}.",
    "note_delete_usage": "Use /note delete <id>.",
    "note_not_found": "Note not found.",
    "note_deleted": "Note deleted.",
    "note_usage": "Use /note add <text>, /note <id>, or /note delete <id>.",
    "notes_empty": "You have no notes.",
    "remind_daily_usage": "Use /remind every day HH:MM <text>.",
    "remind_daily_created": "Daily reminder {reminder_id} created.",
    "remind_weekly_usage": "Use /remind every <weekday> HH:MM <text>.",
    "remind_weekly_created": "Weekly reminder {reminder_id} created.",
    "remind_usage": "Use /remind YYYY-MM-DD HH:MM <text>.",
    "remind_future_usage": "Use a future local time: /remind YYYY-MM-DD HH:MM <text>.",
    "remind_created": "Reminder {reminder_id} set for {date} {time}.",
    "reminders_empty": "You have no reminders.",
    "reminder_not_found": "Reminder not found.",
    "reminder_status_pending": "pending",
    "reminder_status_paused": "paused",
    "reminder_status_sent": "sent",
    "reminder_status_cancelled": "cancelled",
    "reminder_repeat_once": "once",
    "reminder_repeat_daily": "daily",
    "reminder_repeat_weekly": "weekly",
    "reminder_details": (
        "{text}\nDue: {due_time}\nStatus: {status}\nRepeat: {repeat}"
    ),
    "reminder_already": "Reminder is already {status}.",
    "reminder_paused": "Reminder paused.",
    "reminder_resumed": "Reminder resumed.",
    "reminder_complete": "Reminder is already complete.",
    "reminder_cancelled": "Reminder cancelled.",
    "reminder_snooze_usage": (
        "Use /reminder snooze <id> <minutes|hours|days>, for example 30m."
    ),
    "reminder_snoozed": "Reminder snoozed until {due_time} local time.",
    "reminder_edit_usage": "Use /reminder edit <id> <text>.",
    "reminder_edit_denied": "Reminder cannot be edited.",
    "reminder_updated": "Reminder updated.",
    "reminder_usage": (
        "Use /reminder <id> or /reminder <edit|pause|resume|cancel|snooze> ..."
    ),
    "location_removed_with_summary": "Weather location and daily summary removed.",
    "location_removed": "Weather location removed.",
    "location_usage": "Use /location <latitude> <longitude> <name>.",
    "location_changed": "Weather location set to {location}.",
    "location_missing": "Weather location is not set.",
    "location_current": "Weather location is {location} ({latitude:.4f}, {longitude:.4f}).",
    "weather_units_usage": (
        "Use /weather units metric or /weather units imperial."
    ),
    "weather_units_changed": "Weather units changed to {units}.",
    "weather_location_required": "Set a weather location with /location first.",
    "weather_daily_on": "Daily weather summary is on.",
    "weather_daily_off": "Daily weather summary is off.",
    "weather_usage": "Use /weather for today's forecast.",
    "weather_unavailable": "Weather is temporarily unavailable.",
    "information_disabled": "Information requests are not enabled.",
    "information_usage": (
        "Use /ask joke, /ask fact, /ask person <name>, /ask place <name>, "
        "or /ask advice <topic>."
    ),
    "information_unavailable": "Information service is temporarily unavailable.",
    "information_limit": (
        "Weekly information limit reached. It resets on {reset_date} UTC."
    ),
    "greeting": "Hello, {name}!",
    "greeting_anonymous": "Hello!",
    "scheduled_greeting": "Good day, {name}!",
    "profile_fallback": "Message fallback: {locale}",
    "profile": (
        "Name: {name}\nTelegram ID: {telegram_id}\nLanguage: {locale}\n"
        "Greeting time: {greeting_time}\nGreeting days: {greeting_days}\n"
        "Quiet hours: {quiet_hours}\nDaily digest: {digest}\n"
        "Weather location: {weather_location}\nWeather units: {weather_units}\n"
        "Daily weather: {weather_summary}\nTimezone: {timezone}\n"
        "Greetings: {greetings}"
    ),
    "help": (
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
        "/reminder <id> - view or manage a reminder"
    ),
}

UKRAINIAN_MESSAGES = {
    "registration_required": (
        "Ви не зареєстровані. Спочатку надішліть /register."
    ),
    "already_registered": "Ви вже зареєстровані, {name}.",
    "registration_complete": "Дякую, {name}. Реєстрацію завершено.",
    "unknown_command": "Я не знаю такої команди. Спробуйте /help.",
    "language_current": "Ваша мова: {locale}.",
    "language_changed": "Мову змінено на {locale}.",
    "language_usage": "Використайте /language en або /language uk.",
    "style_current": "Ваш стиль привітання: {category}.",
    "style_changed": "Стиль привітання змінено на {category}.",
    "style_usage": (
        "Використайте /style friendly, /style brief або /style cheerful."
    ),
    "greeting_preview": "Попередній перегляд:\n{greeting}",
    "greeting_preview_usage": "Використайте /preview без аргументів.",
    "state_on": "увімкнено",
    "state_off": "вимкнено",
    "state_daily": "щодня",
    "not_set": "не вказано",
    "note_add_usage": "Використайте /note add <текст>.",
    "note_too_long": "Нотатка має містити не більше 500 символів.",
    "note_saved": "Нотатку {note_id} збережено.",
    "note_delete_usage": "Використайте /note delete <id>.",
    "note_not_found": "Нотатку не знайдено.",
    "note_deleted": "Нотатку видалено.",
    "note_usage": "Використайте /note add <текст>, /note <id> або /note delete <id>.",
    "notes_empty": "У вас немає нотаток.",
    "remind_daily_usage": "Використайте /remind every day ГГ:ХХ <текст>.",
    "remind_daily_created": "Щоденне нагадування {reminder_id} створено.",
    "remind_weekly_usage": "Використайте /remind every <день> ГГ:ХХ <текст>.",
    "remind_weekly_created": "Щотижневе нагадування {reminder_id} створено.",
    "remind_usage": "Використайте /remind РРРР-ММ-ДД ГГ:ХХ <текст>.",
    "remind_future_usage": (
        "Вкажіть майбутній місцевий час: /remind РРРР-ММ-ДД ГГ:ХХ <текст>."
    ),
    "remind_created": (
        "Нагадування {reminder_id} встановлено на {date} {time}."
    ),
    "reminders_empty": "У вас немає нагадувань.",
    "reminder_not_found": "Нагадування не знайдено.",
    "reminder_status_pending": "активне",
    "reminder_status_paused": "призупинене",
    "reminder_status_sent": "надіслане",
    "reminder_status_cancelled": "скасоване",
    "reminder_repeat_once": "одноразово",
    "reminder_repeat_daily": "щодня",
    "reminder_repeat_weekly": "щотижня",
    "reminder_details": (
        "{text}\nТермін: {due_time}\nСтатус: {status}\nПовтор: {repeat}"
    ),
    "reminder_already": "Нагадування вже {status}.",
    "reminder_paused": "Нагадування призупинено.",
    "reminder_resumed": "Нагадування відновлено.",
    "reminder_complete": "Нагадування вже завершено.",
    "reminder_cancelled": "Нагадування скасовано.",
    "reminder_snooze_usage": (
        "Використайте /reminder snooze <id> <хвилини|години|дні>, наприклад 30m."
    ),
    "reminder_snoozed": (
        "Нагадування відкладено до {due_time} за місцевим часом."
    ),
    "reminder_edit_usage": "Використайте /reminder edit <id> <текст>.",
    "reminder_edit_denied": "Нагадування не можна змінити.",
    "reminder_updated": "Нагадування оновлено.",
    "reminder_usage": (
        "Використайте /reminder <id> або "
        "/reminder <edit|pause|resume|cancel|snooze> ..."
    ),
    "location_removed_with_summary": (
        "Місце для погоди та щоденний огляд видалено."
    ),
    "location_removed": "Місце для погоди видалено.",
    "location_usage": "Використайте /location <широта> <довгота> <назва>.",
    "location_changed": "Місце для погоди змінено на {location}.",
    "location_missing": "Місце для погоди не вказано.",
    "location_current": "Місце для погоди: {location} ({latitude:.4f}, {longitude:.4f}).",
    "weather_units_usage": (
        "Використайте /weather units metric або /weather units imperial."
    ),
    "weather_units_changed": "Одиниці погоди змінено на {units}.",
    "weather_location_required": "Спочатку вкажіть місце командою /location.",
    "weather_daily_on": "Щоденний огляд погоди увімкнено.",
    "weather_daily_off": "Щоденний огляд погоди вимкнено.",
    "weather_usage": "Використайте /weather для прогнозу на сьогодні.",
    "weather_unavailable": "Погода тимчасово недоступна.",
    "information_disabled": "Інформаційні запити не увімкнено.",
    "information_usage": (
        "Використайте /ask joke, /ask fact, /ask person <ім'я>, "
        "/ask place <місце> або /ask advice <тема>."
    ),
    "information_unavailable": "Інформаційний сервіс тимчасово недоступний.",
    "information_limit": (
        "Тижневий ліміт запитів вичерпано. Він оновиться {reset_date} UTC."
    ),
    "greeting": "Вітаю, {name}!",
    "greeting_anonymous": "Вітаю!",
    "scheduled_greeting": "Добрий день, {name}!",
    "profile_fallback": "Резервна мова повідомлень: {locale}",
    "profile": (
        "Ім'я: {name}\nTelegram ID: {telegram_id}\nМова: {locale}\n"
        "Час привітання: {greeting_time}\nДні привітань: {greeting_days}\n"
        "Тихі години: {quiet_hours}\nЩоденний огляд: {digest}\n"
        "Місце для погоди: {weather_location}\nОдиниці погоди: {weather_units}\n"
        "Щоденна погода: {weather_summary}\nЧасовий пояс: {timezone}\n"
        "Привітання: {greetings}"
    ),
    "help": (
        "Доступні команди:\n"
        "/start - отримати привітання\n"
        "/register - створити профіль\n"
        "/me - показати профіль\n"
        "/language [en|uk] - переглянути або змінити мову\n"
        "/style [friendly|brief|cheerful] - вибрати стиль привітання\n"
        "/preview - переглянути заплановане привітання\n"
        "/time [HH:MM] - переглянути або змінити час привітання\n"
        "/days [daily|weekdays|days...] - вибрати дні привітань\n"
        "/digest [daily|off] - керувати щоденним оглядом\n"
        "/location [lat lon name|off] - керувати місцем для погоди\n"
        "/weather [daily|off] - прогноз або щоденний огляд\n"
        "/ask <joke|fact|person|place|advice> - короткий запит\n"
        "/timezone [area/name] - переглянути або змінити часовий пояс\n"
        "/quiet [start end|off] - керувати тихими годинами\n"
        "/name [name] - переглянути або змінити ім'я\n"
        "/note add <text> - зберегти нотатку\n"
        "/notes - показати нотатки\n"
        "/remind YYYY-MM-DD HH:MM <text> - створити нагадування\n"
        "/remind every day HH:MM <text> - повторювати щодня\n"
        "/remind every <weekday> HH:MM <text> - повторювати щотижня\n"
        "/reminders - показати нагадування\n"
        "/reminder <id> - переглянути або змінити нагадування"
    ),
}


class MessageCatalog:
    def __init__(
        self, catalogs: Mapping[str, Mapping[str, str]] = None
    ) -> None:
        values: Dict[str, Mapping[str, str]] = {
            "en": ENGLISH_MESSAGES,
            "uk": UKRAINIAN_MESSAGES,
        }
        if catalogs:
            values.update(
                {_locale_key(locale): messages for locale, messages in catalogs.items()}
            )
        self.catalogs = values
        self._validate_placeholders()

    @property
    def supported_locales(self) -> Tuple[str, ...]:
        return tuple(sorted(self.catalogs))

    def text(
        self, key: str, locale_code: str = "en", **values: object
    ) -> str:
        if key not in self.catalogs["en"]:
            raise KeyError("unknown message key: {}".format(key))
        locale = self.resolved_locale(key, locale_code)
        template = self.catalogs[locale][key]
        try:
            return template.format(**values)
        except KeyError as error:
            raise ValueError("missing message value") from error

    def resolved_locale(self, key: str, locale_code: str = "en") -> str:
        if key not in self.catalogs["en"]:
            raise KeyError("unknown message key: {}".format(key))
        for candidate in locale_candidates(locale_code):
            messages = self.catalogs.get(candidate)
            if messages is not None and key in messages:
                return candidate
        return "en"

    def _validate_placeholders(self) -> None:
        formatter = Formatter()
        expected = {
            key: {
                field
                for _, field, _, _ in formatter.parse(template)
                if field is not None
            }
            for key, template in self.catalogs["en"].items()
        }
        for locale, messages in self.catalogs.items():
            for key, template in messages.items():
                if key not in expected:
                    raise ValueError("unknown localized message key")
                fields = {
                    field
                    for _, field, _, _ in formatter.parse(template)
                    if field is not None
                }
                if fields != expected[key]:
                    raise ValueError(
                        "localized message placeholders do not match"
                    )


def locale_candidates(locale: str) -> Tuple[str, ...]:
    value = _locale_key(locale)
    language = value.split("-", 1)[0]
    candidates = [value]
    if language != value:
        candidates.append(language)
    if "en" not in candidates:
        candidates.append("en")
    return tuple(candidates)


def _locale_key(locale: str) -> str:
    return (locale or "en").strip().replace("_", "-").lower()
