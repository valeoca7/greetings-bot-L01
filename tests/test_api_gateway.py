import unittest

from greetings_bot.api_gateway import (
    ApiGatewayRequest,
    ApiGatewayRequestError,
    ApiGatewayResponse,
)


class ApiGatewayRequestTest(unittest.TestCase):
    def test_reads_text_body(self):
        request = ApiGatewayRequest.from_event(
            {"body": "hello", "headers": {"X-Test": "value"}}
        )

        self.assertEqual(request.body, "hello")
        self.assertEqual(request.headers["x-test"], "value")

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

    def test_rejects_non_object_headers(self):
        with self.assertRaisesRegex(ApiGatewayRequestError, "headers"):
            ApiGatewayRequest.from_event({"headers": ["bad"]})


class ApiGatewayResponseTest(unittest.TestCase):
    def test_maps_response_fields(self):
        response = ApiGatewayResponse(200, "ok")

        self.assertEqual(
            response.to_dict(),
            {
                "statusCode": 200,
                "headers": {
                    "content-type": "application/json",
                    "cache-control": "no-store",
                    "x-content-type-options": "nosniff",
                },
                "body": "ok",
            },
        )


if __name__ == "__main__":
    unittest.main()
