import unittest

from greetings_bot.messages import MessageCatalog, locale_candidates


class MessageCatalogTest(unittest.TestCase):
    def test_reads_english_messages_with_values(self):
        catalog = MessageCatalog()

        self.assertEqual(
            catalog.text("registration_complete", name="Mira"),
            "Thanks, Mira. You are registered.",
        )
        self.assertEqual(catalog.supported_locales, ("en",))

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


if __name__ == "__main__":
    unittest.main()
