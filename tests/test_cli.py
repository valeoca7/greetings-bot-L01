import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

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

        with TemporaryDirectory() as directory:
            store_path = Path(directory) / "users.json"
            with redirect_stdout(output):
                main(
                    {
                        "TELEGRAM_BOT_TOKEN": "test-token",
                        "USER_STORE_PATH": str(store_path),
                    },
                    ["--update", str(fixture)],
                )

            self.assertTrue(store_path.exists())

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

    def test_keeps_users_between_runs(self):
        fixtures = Path(__file__).parent / "fixtures"
        output = StringIO()

        with TemporaryDirectory() as directory:
            environment = {
                "TELEGRAM_BOT_TOKEN": "test-token",
                "USER_STORE_PATH": str(Path(directory) / "users.json"),
            }
            with redirect_stdout(output):
                main(environment, ["--update", str(fixtures / "start_update.json")])
                main(environment, ["--update", str(fixtures / "me_update.json")])

        self.assertIn("Hello, Mira!", output.getvalue())
        self.assertIn("Name: Mira", output.getvalue())

    def test_keeps_profile_changes_between_runs(self):
        fixtures = Path(__file__).parent / "fixtures"
        output = StringIO()

        with TemporaryDirectory() as directory:
            environment = {
                "TELEGRAM_BOT_TOKEN": "test-token",
                "USER_STORE_PATH": str(Path(directory) / "users.json"),
            }
            with redirect_stdout(output):
                main(environment, ["--update", str(fixtures / "start_update.json")])
                main(environment, ["--update", str(fixtures / "time_update.json")])
                main(environment, ["--update", str(fixtures / "me_update.json")])

        self.assertIn("Greeting time: 18:30", output.getvalue())

    def test_reports_a_broken_user_store(self):
        fixture = Path(__file__).parent / "fixtures" / "start_update.json"
        errors = StringIO()

        with TemporaryDirectory() as directory:
            store_path = Path(directory) / "users.json"
            store_path.write_text("broken")
            with redirect_stderr(errors):
                status = main(
                    {
                        "TELEGRAM_BOT_TOKEN": "test-token",
                        "USER_STORE_PATH": str(store_path),
                    },
                    ["--update", str(fixture)],
                )

        self.assertEqual(status, 1)
        self.assertEqual(errors.getvalue(), "error: unable to process update\n")


if __name__ == "__main__":
    unittest.main()
