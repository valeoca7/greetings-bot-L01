import unittest

from greetings_bot.lambda_handler import handle_event


class LambdaHandlerTest(unittest.TestCase):
    def test_acknowledges_gateway_event(self):
        response = handle_event({"body": "{}"})

        self.assertEqual(response, {"statusCode": 200, "body": ""})


if __name__ == "__main__":
    unittest.main()
