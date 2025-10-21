import unittest

from greetings_bot.greeting_templates import (
    GreetingTemplate,
    GreetingTemplateCatalog,
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


if __name__ == "__main__":
    unittest.main()
