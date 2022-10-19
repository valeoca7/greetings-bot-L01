import unittest

from greetings_bot.api_gateway import ApiGatewayRequest


class ApiGatewayRequestTest(unittest.TestCase):
    def test_reads_text_body(self):
        request = ApiGatewayRequest.from_event({"body": "hello"})

        self.assertEqual(request.body, "hello")

    def test_missing_body_is_none(self):
        request = ApiGatewayRequest.from_event({})

        self.assertIsNone(request.body)


if __name__ == "__main__":
    unittest.main()
