import json
import unittest
from pathlib import Path

from greetings_bot.update_parser import UpdateParseError, load_update, parse_update


class UpdateParserTest(unittest.TestCase):
    def test_loads_an_update_file(self):
        fixture = Path(__file__).parent / "fixtures" / "start_update.json"

        update = load_update(fixture)

        self.assertEqual(update.id, 1001)
        self.assertEqual(update.message.text, "/start")

    def test_parses_a_text_message(self):
        fixture = Path(__file__).parent / "fixtures" / "start_update.json"
        payload = json.loads(fixture.read_text())

        update = parse_update(payload)

        self.assertEqual(update.id, 1001)
        self.assertEqual(update.message.chat_id, 42)
        self.assertEqual(update.message.sender.first_name, "Mira")
        self.assertEqual(update.message.text, "/start")

    def test_parses_an_update_without_a_message(self):
        update = parse_update({"update_id": 1002})

        self.assertIsNone(update.message)

    def test_rejects_a_message_without_an_id(self):
        payload = {
            "update_id": 1003,
            "message": {
                "from": {"id": 42, "first_name": "Mira"},
                "chat": {"id": 42},
                "text": "/start",
            },
        }

        with self.assertRaisesRegex(UpdateParseError, "invalid update payload"):
            parse_update(payload)

    def test_ignores_an_unsupported_update_type(self):
        payload = {
            "update_id": 1004,
            "callback_query": {"id": "callback-1", "data": "unused"},
        }

        update = parse_update(payload)

        self.assertIsNone(update.message)


if __name__ == "__main__":
    unittest.main()
