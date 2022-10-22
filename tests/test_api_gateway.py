import unittest

from greetings_bot.api_gateway import ApiGatewayRequest, ApiGatewayRequestError


class ApiGatewayRequestTest(unittest.TestCase):
    def test_reads_text_body(self):
        request = ApiGatewayRequest.from_event({"body": "hello"})

        self.assertEqual(request.body, "hello")

    def test_missing_body_is_none(self):
        request = ApiGatewayRequest.from_event({})

        self.assertIsNone(request.body)

    def test_decodes_base64_body(self):
        request = ApiGatewayRequest.from_event(
            {"body": "aGVsbG8=", "isBase64Encoded": True}
        )

        self.assertEqual(request.body, "hello")

    def test_reads_json_body(self):
        request = ApiGatewayRequest.from_event({"body": '{"update_id": 1}'})

        self.assertEqual(request.json_body(), {"update_id": 1})

    def test_rejects_invalid_json(self):
        request = ApiGatewayRequest.from_event({"body": "{"})

        with self.assertRaisesRegex(ApiGatewayRequestError, "must be JSON"):
            request.json_body()


if __name__ == "__main__":
    unittest.main()
