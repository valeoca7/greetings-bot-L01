import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from greetings_bot.cli import main


class CliTest(unittest.TestCase):
    def test_prints_application_name(self):
        output = StringIO()

        with redirect_stdout(output):
            status = main({"TELEGRAM_BOT_TOKEN": "test-token"}, [])

        self.assertEqual(output.getvalue(), "greetings-bot is configured\n")
        self.assertEqual(status, 0)

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

    def test_reports_an_unreadable_update_file(self):
        errors = StringIO()

        with redirect_stderr(errors):
            status = main(
                {"TELEGRAM_BOT_TOKEN": "test-token"},
                ["--update", "missing-update.json"],
            )

        self.assertEqual(status, 1)
        self.assertEqual(errors.getvalue(), "error: unable to process update\n")


if __name__ == "__main__":
    unittest.main()
