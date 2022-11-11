import unittest
from pathlib import Path


class SamTemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = Path("template.yaml").read_text()

    def test_defines_python_webhook_function(self):
        self.assertIn("Type: AWS::Serverless::Function", self.template)
        self.assertIn("Runtime: python3.9", self.template)
        self.assertIn("greetings_bot.lambda_handler.handle_event", self.template)

    def test_exposes_post_webhook(self):
        self.assertIn("Path: /telegram/webhook", self.template)
        self.assertIn("Method: post", self.template)


if __name__ == "__main__":
    unittest.main()
