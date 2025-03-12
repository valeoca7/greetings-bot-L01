import json
import unittest

from greetings_bot.admin_api import AdminRequest, AdminRequestError, AdminResponse


class AdminRequestTest(unittest.TestCase):
    def test_reads_http_api_request_fields(self):
        request = AdminRequest.from_event(
            {
                "rawPath": "/admin/health",
                "headers": {"Authorization": "Bearer secret"},
                "queryStringParameters": {"status": "active", "limit": "10"},
                "requestContext": {"http": {"method": "GET"}},
            }
        )

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.path, "/admin/health")
        self.assertEqual(request.headers["authorization"], "Bearer secret")
        self.assertEqual(request.query, {"status": "active", "limit": "10"})

    def test_supports_rest_api_request_fields(self):
        request = AdminRequest.from_event(
            {"path": "/admin/stats", "httpMethod": "GET", "headers": {}}
        )

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.path, "/admin/stats")

    def test_rejects_incomplete_requests(self):
        for event in ({}, {"httpMethod": "GET"}, {"path": "/admin/health"}):
            with self.subTest(event=event):
                with self.assertRaises(AdminRequestError):
                    AdminRequest.from_event(event)

    def test_rejects_non_object_query_parameters(self):
        with self.assertRaises(AdminRequestError):
            AdminRequest.from_event(
                {
                    "path": "/admin/users",
                    "httpMethod": "GET",
                    "queryStringParameters": "status=active",
                }
            )


class AdminResponseTest(unittest.TestCase):
    def test_serializes_a_json_response(self):
        response = AdminResponse(200, {"status": "ok"}).to_dict()

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), {"status": "ok"})
        self.assertEqual(response["headers"]["content-type"], "application/json")
        self.assertEqual(response["headers"]["cache-control"], "no-store")
        self.assertEqual(
            response["headers"]["x-content-type-options"], "nosniff"
        )


if __name__ == "__main__":
    unittest.main()
