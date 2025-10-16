import unittest

from greetings_bot.messages import MessageCatalog, locale_candidates


class MessageCatalogTest(unittest.TestCase):
    def test_reads_english_messages_with_values(self):
        catalog = MessageCatalog()

        self.assertEqual(
            catalog.text("registration_complete", name="Mira"),
            "Thanks, Mira. You are registered.",
        )
        self.assertEqual(catalog.supported_locales, ("en", "uk"))

    def test_falls_back_from_region_to_language_then_english(self):
        catalog = MessageCatalog(
            {"fr": {"registration_required": "Inscription requise."}}
        )

        self.assertEqual(
            catalog.text("registration_required", "fr-CA"),
            "Inscription requise.",
        )
        self.assertEqual(
            catalog.text("unknown_command", "fr-CA"),
            "I don't know that command. Try /help.",
        )
        self.assertEqual(
            catalog.resolved_locale("registration_required", "fr-CA"), "fr"
        )
        self.assertEqual(catalog.resolved_locale("help", "fr-CA"), "en")
        self.assertEqual(
            locale_candidates("pt_BR"), ("pt-br", "pt", "en")
        )

    def test_rejects_mismatched_localized_placeholders(self):
        with self.assertRaises(ValueError):
            MessageCatalog(
                {"fr": {"registration_complete": "Bienvenue {user}."}}
            )

    def test_rejects_missing_render_values(self):
        with self.assertRaises(ValueError):
            MessageCatalog().text("registration_complete")

    def test_includes_ukrainian_and_regional_fallback(self):
        catalog = MessageCatalog()

        self.assertEqual(
            catalog.text("registration_complete", "uk-UA", name="Міра"),
            "Дякую, Міра. Реєстрацію завершено.",
        )
        self.assertIn("Доступні команди", catalog.text("help", "uk"))


if __name__ == "__main__":
    unittest.main()
