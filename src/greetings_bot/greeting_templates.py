from dataclasses import dataclass
from typing import Iterable, Tuple

from greetings_bot.messages import locale_candidates


TEMPLATE_CATEGORIES = ("friendly", "brief", "cheerful")
MAX_TEMPLATE_LENGTH = 240


@dataclass(frozen=True)
class GreetingTemplate:
    category: str
    locale: str
    text: str

    def __post_init__(self) -> None:
        if self.category not in TEMPLATE_CATEGORIES:
            raise ValueError("unknown greeting template category")
        if not self.locale.strip():
            raise ValueError("template locale is required")
        if not self.text.strip() or len(self.text) > MAX_TEMPLATE_LENGTH:
            raise ValueError("invalid greeting template text")


BUILTIN_TEMPLATES = (
    GreetingTemplate("friendly", "en", "Good day, {name}!"),
    GreetingTemplate("friendly", "uk", "Добрий день, {name}!"),
    GreetingTemplate("brief", "en", "Hello, {name}."),
    GreetingTemplate("brief", "uk", "Вітаю, {name}."),
    GreetingTemplate("cheerful", "en", "Hope your day starts well, {name}!"),
    GreetingTemplate("cheerful", "uk", "Гарного початку дня, {name}!"),
)


class GreetingTemplateCatalog:
    def __init__(
        self, templates: Iterable[GreetingTemplate] = BUILTIN_TEMPLATES
    ) -> None:
        values = {}
        for template in templates:
            key = (template.category, template.locale.lower())
            if key in values:
                raise ValueError("duplicate greeting template")
            values[key] = template
        self.templates = values

    @property
    def categories(self) -> Tuple[str, ...]:
        return tuple(
            category
            for category in TEMPLATE_CATEGORIES
            if any(key[0] == category for key in self.templates)
        )

    def get(self, category: str, locale: str) -> GreetingTemplate:
        for candidate in locale_candidates(locale):
            template = self.templates.get((category, candidate))
            if template is not None:
                return template
        raise KeyError("greeting template not found")
