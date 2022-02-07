import unittest
from contextlib import redirect_stdout
from io import StringIO

from greetings_bot.cli import main


class CliTest(unittest.TestCase):
    def test_prints_application_name(self):
        output = StringIO()

        with redirect_stdout(output):
            main()

        self.assertEqual(output.getvalue(), "greetings-bot\n")


if __name__ == "__main__":
    unittest.main()
