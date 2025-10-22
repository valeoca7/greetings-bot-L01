import unittest

from greetings_bot.greeting_templates import (
    GreetingTemplate,
    GreetingTemplateCatalog,
    GreetingTemplateRenderer,
)


class GreetingTemplateTest(unittest.TestCase):
    def test_rejects_unknown_categories_and_invalid_text(self):
        with self.assertRaises(ValueError):
            GreetingTemplate("formal", "en", "Hello")
        with self.assertRaises(ValueError):
            GreetingTemplate("friendly", "en", " ")

    def test_lists_built_in_categories_in_display_order(self):
        catalog = GreetingTemplateCatalog()

        self.assertEqual(
            catalog.categories, ("friendly", "brief", "cheerful")
        )

    def test_selects_a_locale_and_falls_back_to_english(self):
        catalog = GreetingTemplateCatalog()

        self.assertEqual(
            catalog.get("friendly", "uk-UA").text,
            "Добрий день, {name}!",
        )
        self.assertEqual(
            catalog.get("brief", "fr").text,
            "Hello, {name}.",
        )

    def test_rejects_duplicate_templates(self):
        template = GreetingTemplate("friendly", "en", "Hello, {name}!")

        with self.assertRaises(ValueError):
            GreetingTemplateCatalog((template, template))


class GreetingTemplateRendererTest(unittest.TestCase):
    def test_renders_allowlisted_values(self):
        template = GreetingTemplate(
            "friendly", "en", "Good {weekday}, {name}! Today is {date}."
        )

        text = GreetingTemplateRenderer().render(
            template,
            {"name": "Mira", "weekday": "Monday", "date": "2025-10-20"},
        )

        self.assertEqual(text, "Good Monday, Mira! Today is 2025-10-20.")

    def test_rejects_unknown_or_traversed_values(self):
        renderer = GreetingTemplateRenderer()

        with self.assertRaises(ValueError):
            renderer.render(
                GreetingTemplate("brief", "en", "{note}"), {"note": "private"}
            )
        with self.assertRaises(ValueError):
            renderer.render(
                GreetingTemplate("brief", "en", "{name.__class__}"),
                {"name": "Mira"},
            )

    def test_rejects_missing_values(self):
        template = GreetingTemplate("brief", "en", "Hello, {name}.")

        with self.assertRaises(ValueError):
            GreetingTemplateRenderer().render(template, {})

    def test_bounds_the_rendered_greeting(self):
        template = GreetingTemplate("brief", "en", "Hello, {name}.")

        with self.assertRaises(ValueError):
            GreetingTemplateRenderer(max_length=11).render(
                template, {"name": "Mira"}
            )


if __name__ == "__main__":
    unittest.main()
