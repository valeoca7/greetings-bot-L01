import unittest

from greetings_bot.admin import AdminApplication
from greetings_bot.admin_api import AdminRequest
from greetings_bot.users import InMemoryUserRepository, User


class FixedAuthorizer:
    def __init__(self, allowed):
        self.allowed = allowed

    def authorize(self, request):
        self.request = request
        return self.allowed


class AdminApplicationTest(unittest.TestCase):
    def test_denies_requests_before_routing(self):
        request = AdminRequest("GET", "/admin/health", {})

        response = AdminApplication(
            FixedAuthorizer(False), InMemoryUserRepository()
        ).handle(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body, {"error": "unauthorized"})

    def test_reports_service_health(self):
        response = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository()
        ).handle(AdminRequest("GET", "/admin/health", {}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["status"], "ok")
        self.assertIn("version", response.body)

    def test_reports_a_user_count(self):
        users = InMemoryUserRepository()
        users.save(User(42, 42, "Mira"))

        response = AdminApplication(FixedAuthorizer(True), users).handle(
            AdminRequest("GET", "/admin/stats", {})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, {"users": 1})

    def test_rejects_unknown_routes_and_write_methods(self):
        app = AdminApplication(FixedAuthorizer(True), InMemoryUserRepository())

        missing = app.handle(AdminRequest("GET", "/admin/missing", {}))
        write = app.handle(AdminRequest("POST", "/admin/health", {}))

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(write.status_code, 405)


if __name__ == "__main__":
    unittest.main()
