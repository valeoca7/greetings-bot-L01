import unittest

from greetings_bot.commands import Command, parse_command


class CommandTest(unittest.TestCase):
    def test_parses_arguments(self):
        command = parse_command("/start one two")

        self.assertEqual(command, Command(name="start", arguments=("one", "two")))

    def test_removes_bot_name(self):
        command = parse_command("/help@my_greetings_bot")

        self.assertEqual(command.name, "help")

    def test_ignores_plain_text(self):
        self.assertIsNone(parse_command("hello"))


if __name__ == "__main__":
    unittest.main()
