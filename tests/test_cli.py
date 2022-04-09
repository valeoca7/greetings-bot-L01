import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from greetings_bot.cli import main


class CliTest(unittest.TestCase):
    def test_prints_application_name(self):
        output = StringIO()

        with redirect_stdout(output):
            main({"TELEGRAM_BOT_TOKEN": "test-token"}, [])

        self.assertEqual(output.getvalue(), "greetings-bot is configured\n")

    def test_processes_an_update_file(self):
        fixture = Path(__file__).parent / "fixtures" / "start_update.json"
        output = StringIO()

        with redirect_stdout(output):
            main(
                {"TELEGRAM_BOT_TOKEN": "test-token"},
                ["--update", str(fixture)],
            )

        self.assertEqual(
            output.getvalue(),
            '{"chat_id": 42, "text": "Hello, Mira!"}\n',
        )


if __name__ == "__main__":
    unittest.main()
