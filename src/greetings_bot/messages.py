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
    "help": (
        "Available commands:\n"
        "/start - get a greeting\n"
        "/register - create a profile\n"
        "/me - show your profile\n"
        "/language [en|uk] - show or change language\n"
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
    "help": (
        "Доступні команди:\n"
        "/start - отримати привітання\n"
        "/register - створити профіль\n"
        "/me - показати профіль\n"
        "/language [en|uk] - переглянути або змінити мову\n"
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
        template = self.catalogs["en"][key]
        for candidate in locale_candidates(locale_code):
            messages = self.catalogs.get(candidate)
            if messages is not None and key in messages:
                template = messages[key]
                break
        try:
            return template.format(**values)
        except KeyError as error:
            raise ValueError("missing message value") from error

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
