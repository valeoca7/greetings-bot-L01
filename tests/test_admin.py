import unittest
from datetime import datetime, timezone

from greetings_bot.admin import AdminApplication
from greetings_bot.admin_api import (
    AdminRequest,
    HtmlResponse,
    JsonDownloadResponse,
)
from greetings_bot.admin_delivery import DeliveryAdminError, DeliveryQueueSummary
from greetings_bot.admin_config import DashboardConfig
from greetings_bot.clock import FixedClock
from greetings_bot.configuration_audit import (
    AuditRecord,
    InMemoryAuditRepository,
)
from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.user_data import UserDataExporter
from greetings_bot.users import InMemoryUserRepository, User


class FixedAuthorizer:
    def __init__(self, allowed):
        self.allowed = allowed

    def authorize(self, request):
        self.request = request
        return self.allowed


class FakeDeliveryOperations:
    def summary(self):
        return DeliveryQueueSummary(12, 3, 2)

    def start_redrive(self, max_rate):
        self.max_rate = max_rate
        return "task-123"


class FakeDeletionService:
    def request(self, telegram_id):
        self.requested_id = telegram_id
        return "confirmation-token-value"

    def confirm(self, telegram_id, token):
        self.confirmed = (telegram_id, token)
        return type("Request", (), {"status": "confirmed"})()

    def execute(self, telegram_id):
        self.executed_id = telegram_id
        return type("Request", (), {"status": "completed"})()


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

    def test_denies_dashboard_before_loading_summary_data(self):
        class UntouchedUsers:
            def all(self):
                raise AssertionError("dashboard data should not be read")

        response = AdminApplication(
            FixedAuthorizer(False), UntouchedUsers(), FakeDeliveryOperations()
        ).handle(AdminRequest("GET", "/admin/dashboard", {}))

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

    def test_downloads_one_users_export(self):
        users = InMemoryUserRepository()
        users.save(User(42, 4200, "Mira"))
        exporter = UserDataExporter(
            users,
            InMemoryNoteRepository(),
            InMemoryReminderRepository(),
        )
        app = AdminApplication(
            FixedAuthorizer(True),
            users,
            exporter=exporter,
            clock=FixedClock(
                datetime(2025, 9, 8, 3, 0, tzinfo=timezone.utc)
            ),
        )

        response = app.handle(
            AdminRequest("GET", "/admin/users/42/export", {})
        )

        self.assertIsInstance(response, JsonDownloadResponse)
        self.assertIn('"schema_version":1', response.body)
        self.assertIn('"telegram_id":42', response.body)
        self.assertNotIn("4200", response.body)

    def test_handles_missing_and_invalid_user_exports(self):
        users = InMemoryUserRepository()
        exporter = UserDataExporter(
            users,
            InMemoryNoteRepository(),
            InMemoryReminderRepository(),
        )
        app = AdminApplication(
            FixedAuthorizer(True), users, exporter=exporter
        )

        missing = app.handle(
            AdminRequest("GET", "/admin/users/42/export", {})
        )
        invalid = app.handle(
            AdminRequest("GET", "/admin/users/nope/export", {})
        )

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(invalid.status_code, 400)

    def test_requests_confirms_and_executes_user_deletion(self):
        deletion = FakeDeletionService()
        app = AdminApplication(
            FixedAuthorizer(True),
            InMemoryUserRepository(),
            deletion=deletion,
        )

        requested = app.handle(
            AdminRequest("POST", "/admin/users/42/deletion", {})
        )
        confirmed = app.handle(
            AdminRequest(
                "POST",
                "/admin/users/42/deletion/confirm",
                {},
                body='{"confirmation_token":"confirmation-token-value"}',
            )
        )
        completed = app.handle(
            AdminRequest(
                "POST", "/admin/users/42/deletion/execute", {}
            )
        )

        self.assertEqual(requested.status_code, 201)
        self.assertEqual(
            requested.body["confirmation_token"],
            "confirmation-token-value",
        )
        self.assertEqual(confirmed.body, {"status": "confirmed"})
        self.assertEqual(completed.body, {"status": "completed"})
        self.assertEqual(deletion.requested_id, 42)
        self.assertEqual(
            deletion.confirmed, (42, "confirmation-token-value")
        )
        self.assertEqual(deletion.executed_id, 42)

    def test_rejects_invalid_deletion_routes_and_confirmation(self):
        app = AdminApplication(
            FixedAuthorizer(True),
            InMemoryUserRepository(),
            deletion=FakeDeletionService(),
        )

        invalid_id = app.handle(
            AdminRequest("POST", "/admin/users/nope/deletion", {})
        )
        missing_token = app.handle(
            AdminRequest(
                "POST",
                "/admin/users/42/deletion/confirm",
                {},
                body="{}",
            )
        )
        wrong_method = app.handle(
            AdminRequest("GET", "/admin/users/42/deletion", {})
        )

        self.assertEqual(invalid_id.status_code, 400)
        self.assertEqual(missing_token.status_code, 400)
        self.assertEqual(wrong_method.status_code, 405)

    def test_handles_missing_and_invalid_user_ids(self):
        app = AdminApplication(FixedAuthorizer(True), InMemoryUserRepository())

        missing = app.handle(AdminRequest("GET", "/admin/users/42", {}))
        invalid = app.handle(AdminRequest("GET", "/admin/users/not-a-number", {}))

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(invalid.status_code, 400)

    def test_reports_delivery_queue_health(self):
        app = AdminApplication(
            FixedAuthorizer(True),
            InMemoryUserRepository(),
            FakeDeliveryOperations(),
        )

        response = app.handle(AdminRequest("GET", "/admin/delivery", {}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["failed"], 2)

    def test_handles_delivery_provider_failure(self):
        class FailedOperations(FakeDeliveryOperations):
            def summary(self):
                raise DeliveryAdminError("offline")

        app = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository(), FailedOperations()
        )

        response = app.handle(AdminRequest("GET", "/admin/delivery", {}))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, {"error": "delivery admin unavailable"})

    def test_renders_the_authorized_dashboard_summary(self):
        users = InMemoryUserRepository()
        users.save(User(42, 42, "Mira"))
        users.save(User(7, 7, "Sam", enabled=False))
        app = AdminApplication(
            FixedAuthorizer(True), users, FakeDeliveryOperations()
        )

        response = app.handle(AdminRequest("GET", "/admin/dashboard", {}))

        self.assertIsInstance(response, HtmlResponse)
        self.assertEqual(response.status_code, 200)
        self.assertIn('data-metric="users">2<', response.body)
        self.assertIn('data-metric="active-users">1<', response.body)
        self.assertIn('data-metric="failed">2<', response.body)

    def test_dashboard_survives_delivery_summary_failure(self):
        class FailedOperations(FakeDeliveryOperations):
            def summary(self):
                raise DeliveryAdminError("offline")

        app = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository(), FailedOperations()
        )

        response = app.handle(AdminRequest("GET", "/admin/dashboard", {}))

        self.assertEqual(response.status_code, 200)
        self.assertIn("Delivery summary unavailable", response.body)

    def test_renders_filtered_dashboard_user_page(self):
        users = InMemoryUserRepository()
        users.save(User(42, 42, "Mira"))
        users.save(User(7, 7, "Sam", enabled=False))
        app = AdminApplication(FixedAuthorizer(True), users)

        response = app.handle(
            AdminRequest(
                "GET",
                "/admin/dashboard/users",
                {},
                {"status": "active"},
            )
        )

        self.assertIsInstance(response, HtmlResponse)
        self.assertIn("Mira", response.body)
        self.assertNotIn(">Sam<", response.body)

    def test_rejects_invalid_dashboard_user_filters(self):
        response = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository()
        ).handle(
            AdminRequest(
                "GET", "/admin/dashboard/users", {}, {"limit": "lots"}
            )
        )

        self.assertEqual(response.status_code, 400)

    def test_renders_dashboard_user_details(self):
        users = InMemoryUserRepository()
        users.save(User(42, 42, "Mira", greeting_time="18:30"))

        response = AdminApplication(FixedAuthorizer(True), users).handle(
            AdminRequest("GET", "/admin/dashboard/users/42", {})
        )

        self.assertIsInstance(response, HtmlResponse)
        self.assertIn("Mira", response.body)
        self.assertIn("18:30", response.body)

    def test_handles_missing_dashboard_user_details(self):
        app = AdminApplication(FixedAuthorizer(True), InMemoryUserRepository())

        missing = app.handle(
            AdminRequest("GET", "/admin/dashboard/users/42", {})
        )
        invalid = app.handle(
            AdminRequest("GET", "/admin/dashboard/users/nope", {})
        )

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(invalid.status_code, 400)

    def test_renders_dashboard_configuration(self):
        config = DashboardConfig(False, 5, "model-v1", 20, 60, 24, False)
        app = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository(), None, config
        )

        response = app.handle(
            AdminRequest("GET", "/admin/dashboard/config", {})
        )

        self.assertIsInstance(response, HtmlResponse)
        self.assertIn("model-v1", response.body)
        self.assertIn("Disabled", response.body)
        self.assertIn("Message languages", response.body)
        self.assertIn("en, uk", response.body)
        self.assertIn("Message fallback", response.body)

    def test_renders_dashboard_delivery_operations(self):
        app = AdminApplication(
            FixedAuthorizer(True),
            InMemoryUserRepository(),
            FakeDeliveryOperations(),
        )

        response = app.handle(
            AdminRequest("GET", "/admin/dashboard/delivery", {})
        )

        self.assertIsInstance(response, HtmlResponse)
        self.assertEqual(response.status_code, 200)
        self.assertIn('data-metric="failed">2<', response.body)

    def test_starts_redrive_from_the_dashboard_form(self):
        operations = FakeDeliveryOperations()
        app = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository(), operations
        )
        request = AdminRequest(
            "POST",
            "/admin/dashboard/delivery/redrive",
            {"content-type": "application/x-www-form-urlencoded"},
            body="rate=25&confirm=redrive_failed_deliveries",
        )

        response = app.handle(request)

        self.assertIsInstance(response, HtmlResponse)
        self.assertEqual(response.status_code, 202)
        self.assertIn("Redrive task started", response.body)
        self.assertEqual(operations.max_rate, 25)

    def test_rejects_an_unconfirmed_dashboard_redrive(self):
        app = AdminApplication(
            FixedAuthorizer(True),
            InMemoryUserRepository(),
            FakeDeliveryOperations(),
        )
        request = AdminRequest(
            "POST",
            "/admin/dashboard/delivery/redrive",
            {"content-type": "application/x-www-form-urlencoded"},
            body="rate=25",
        )

        response = app.handle(request)

        self.assertEqual(response.status_code, 400)

    def test_keeps_an_accepted_redrive_success_when_refresh_fails(self):
        class FailingRefreshOperations(FakeDeliveryOperations):
            def __init__(self):
                self.summary_calls = 0

            def summary(self):
                self.summary_calls += 1
                if self.summary_calls > 1:
                    raise DeliveryAdminError("offline")
                return super().summary()

        operations = FailingRefreshOperations()
        app = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository(), operations
        )
        request = AdminRequest(
            "POST",
            "/admin/dashboard/delivery/redrive",
            {"content-type": "application/x-www-form-urlencoded"},
            body="rate=25&confirm=redrive_failed_deliveries",
        )

        response = app.handle(request)

        self.assertEqual(response.status_code, 202)
        self.assertIn("Redrive task started", response.body)
        self.assertEqual(operations.max_rate, 25)

    def test_starts_an_explicitly_confirmed_redrive(self):
        operations = FakeDeliveryOperations()
        app = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository(), operations
        )
        request = AdminRequest(
            "POST",
            "/admin/delivery/redrive",
            {},
            {},
            '{"confirm":"redrive_failed_deliveries","rate":25}',
        )

        response = app.handle(request)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.body, {"task": "task-123", "rate": 25})
        self.assertEqual(operations.max_rate, 25)

    def test_rejects_unconfirmed_redrive_requests(self):
        app = AdminApplication(
            FixedAuthorizer(True),
            InMemoryUserRepository(),
            FakeDeliveryOperations(),
        )

        for body in ('{"rate":25}', '{"confirm":"redrive_failed_deliveries"}'):
            with self.subTest(body=body):
                response = app.handle(
                    AdminRequest(
                        "POST", "/admin/delivery/redrive", {}, {}, body
                    )
                )
                self.assertEqual(response.status_code, 400)

    def test_lists_filtered_configuration_audit_records(self):
        audit = InMemoryAuditRepository()
        audit.save(
            AuditRecord(
                "audit-1",
                datetime(2025, 12, 10, 20, 0, tzinfo=timezone.utc),
                "configuration",
                "flags_loaded",
                "deployment",
                "request-1",
                ("greeting_previews",),
            )
        )
        app = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository(), audit=audit
        )

        response = app.handle(
            AdminRequest(
                "GET",
                "/admin/audit",
                {},
                {"category": "configuration", "limit": "10"},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["items"][0]["id"], "audit-1")
        self.assertNotIn("values", response.body["items"][0])

    def test_handles_unavailable_or_invalid_audit_queries(self):
        unavailable = AdminApplication(
            FixedAuthorizer(True), InMemoryUserRepository()
        ).handle(AdminRequest("GET", "/admin/audit", {}))
        invalid = AdminApplication(
            FixedAuthorizer(True),
            InMemoryUserRepository(),
            audit=InMemoryAuditRepository(),
        ).handle(
            AdminRequest("GET", "/admin/audit", {}, {"limit": "all"})
        )

        self.assertEqual(unavailable.status_code, 503)
        self.assertEqual(invalid.status_code, 400)

    def test_rejects_unknown_routes_and_write_methods(self):
        app = AdminApplication(FixedAuthorizer(True), InMemoryUserRepository())

        missing = app.handle(AdminRequest("GET", "/admin/missing", {}))
        write = app.handle(AdminRequest("POST", "/admin/health", {}))

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(write.status_code, 405)


if __name__ == "__main__":
    unittest.main()
