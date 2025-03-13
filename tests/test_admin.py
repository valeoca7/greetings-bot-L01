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

    def test_denies_user_lists_before_repository_access(self):
        class UntouchedUsers:
            def all(self):
                raise AssertionError("repository should not be read")

        response = AdminApplication(
            FixedAuthorizer(False), UntouchedUsers()
        ).handle(AdminRequest("GET", "/admin/users", {}))

        self.assertEqual(response.status_code, 401)

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

    def test_lists_filtered_users_with_a_next_cursor(self):
        users = InMemoryUserRepository()
        users.save(User(42, 42, "Mira"))
        users.save(User(7, 7, "Sam", enabled=False))
        users.save(User(99, 99, "Amira"))
        request = AdminRequest(
            "GET", "/admin/users", {}, {"q": "mira", "limit": "1"}
        )

        response = AdminApplication(FixedAuthorizer(True), users).handle(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["items"][0]["id"], 42)
        self.assertIsNotNone(response.body["next_cursor"])

    def test_rejects_invalid_user_list_filters(self):
        response = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository()
        ).handle(
            AdminRequest("GET", "/admin/users", {}, {"limit": "huge"})
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("limit", response.body["error"])

    def test_returns_one_user_with_preferences(self):
        users = InMemoryUserRepository()
        users.save(User(42, 4200, "Mira", greeting_time="18:30"))

        response = AdminApplication(FixedAuthorizer(True), users).handle(
            AdminRequest("GET", "/admin/users/42", {})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["id"], 42)
        self.assertEqual(response.body["preferences"]["greeting_time"], "18:30")
        self.assertNotIn("chat_id", response.body)

    def test_handles_missing_and_invalid_user_ids(self):
        app = AdminApplication(FixedAuthorizer(True), InMemoryUserRepository())

        missing = app.handle(AdminRequest("GET", "/admin/users/42", {}))
        invalid = app.handle(AdminRequest("GET", "/admin/users/not-a-number", {}))

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(invalid.status_code, 400)

    def test_rejects_unknown_routes_and_write_methods(self):
        app = AdminApplication(FixedAuthorizer(True), InMemoryUserRepository())

        missing = app.handle(AdminRequest("GET", "/admin/missing", {}))
        write = app.handle(AdminRequest("POST", "/admin/health", {}))

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(write.status_code, 405)


if __name__ == "__main__":
    unittest.main()
