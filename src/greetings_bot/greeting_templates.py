from dataclasses import dataclass
from string import Formatter
from typing import Iterable, Mapping, Tuple

from greetings_bot.messages import locale_candidates


TEMPLATE_CATEGORIES = ("friendly", "brief", "cheerful")
MAX_TEMPLATE_LENGTH = 240
MAX_RENDERED_LENGTH = 320
ALLOWED_TEMPLATE_VARIABLES = ("name", "weekday", "date")


def _template_variables(text: str) -> Tuple[str, ...]:
    fields = []
    try:
        parts = Formatter().parse(text)
        for _, field, format_spec, conversion in parts:
            if field is None:
                continue
            if (
                field not in ALLOWED_TEMPLATE_VARIABLES
                or format_spec
                or conversion
            ):
                raise ValueError("unsafe greeting template variable")
            if field not in fields:
                fields.append(field)
    except ValueError as error:
        raise ValueError("invalid greeting template") from error
    return tuple(fields)


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
        _template_variables(self.text)


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


class GreetingTemplateRenderer:
    def __init__(self, max_length: int = MAX_RENDERED_LENGTH) -> None:
        if max_length < 1:
            raise ValueError("rendered greeting limit must be positive")
        self.max_length = max_length

    def variables(self, template: GreetingTemplate) -> Tuple[str, ...]:
        return _template_variables(template.text)

    def render(
        self, template: GreetingTemplate, values: Mapping[str, object]
    ) -> str:
        fields = self.variables(template)
        if any(field not in values for field in fields):
            raise ValueError("missing greeting template value")
        rendered = template.text.format(
            **{field: str(values[field]) for field in fields}
        )
        if len(rendered) > self.max_length:
            raise ValueError("rendered greeting is too long")
        return rendered
