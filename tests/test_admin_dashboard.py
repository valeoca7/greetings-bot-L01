import unittest
from datetime import datetime, timezone

from greetings_bot.admin_dashboard import (
    DashboardSnapshot,
    render_dashboard,
    render_user_detail,
    render_user_list,
    render_config,
    render_audit,
    render_delivery,
)
from greetings_bot.configuration_audit import (
    AuditPage,
    AuditQuery,
    AuditRecord,
)
from greetings_bot.admin_config import DashboardConfig
from greetings_bot.admin_delivery import DeliveryQueueSummary
from greetings_bot.admin_users import AdminUserPage, AdminUserQuery


class AdminDashboardTest(unittest.TestCase):
    def test_renders_a_semantic_dashboard_shell(self):
        page = render_dashboard("0.30.0")

        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("<title>Greetings Bot Admin</title>", page)
        self.assertIn('<meta name="viewport"', page)
        self.assertIn("<nav", page)
        self.assertIn("<main", page)
        self.assertIn('href="#main-content"', page)
        self.assertIn('id="main-content"', page)
        self.assertIn(":focus-visible", page)
        self.assertIn(
            '<a href="/admin/dashboard" aria-current="page">Overview</a>', page
        )
        self.assertIn("Version 0.30.0", page)
        self.assertNotIn("<script", page)

    def test_escapes_the_rendered_version(self):
        page = render_dashboard("<unsafe>")

        self.assertIn("Version &lt;unsafe&gt;", page)
        self.assertNotIn("Version <unsafe>", page)

    def test_renders_user_and_delivery_summary_cards(self):
        snapshot = DashboardSnapshot(
            users=18,
            active_users=15,
            disabled_users=3,
            pending=7,
            in_flight=2,
            failed=1,
        )

        page = render_dashboard("0.30.0", snapshot)

        self.assertIn('data-metric="users">18<', page)
        self.assertIn('data-metric="active-users">15<', page)
        self.assertIn('data-metric="disabled-users">3<', page)
        self.assertIn('data-metric="pending">7<', page)
        self.assertIn('data-metric="failed">1<', page)

    def test_marks_delivery_summary_unavailable(self):
        page = render_dashboard(
            "0.30.0", DashboardSnapshot(2, 2, 0)
        )

        self.assertIn("Delivery summary unavailable", page)

    def test_renders_filtered_user_table_and_next_link(self):
        users = AdminUserPage(
            (
                {
                    "id": 42,
                    "name": "Mira <Admin>",
                    "status": "active",
                    "timezone": "America/Vancouver",
                    "greeting_time": "18:30",
                },
            ),
            True,
            "next-page-token",
        )
        query = AdminUserQuery(term="Mira", status="active", limit=10)

        page = render_user_list("0.31.0", users, query)

        self.assertIn("User administration", page)
        self.assertIn("Mira &lt;Admin&gt;", page)
        self.assertNotIn("Mira <Admin>", page)
        self.assertIn('value="Mira"', page)
        self.assertIn('for="user-search"', page)
        self.assertIn('aria-label="Filter users"', page)
        self.assertIn('<option value="active" selected>', page)
        self.assertIn("cursor=next-page-token", page)
        self.assertIn('/admin/dashboard/users/42', page)
        self.assertIn('<caption class="visually-hidden">Matching users</caption>', page)
        self.assertIn('<th scope="col">ID</th>', page)
        self.assertIn('class="table-region"', page)
        self.assertIn(
            '<a href="/admin/dashboard/users" aria-current="page">Users</a>', page
        )
        self.assertNotIn("chat_id", page)

    def test_renders_escaped_user_preference_details(self):
        detail = {
            "id": 42,
            "name": "Mira <Owner>",
            "status": "active",
            "preferences": {
                "locale": "en",
                "timezone": "America/Vancouver",
                "greeting_time": "18:30",
                "greeting_template_category": "cheerful",
                "greeting_days": ["mon", "wed", "fri"],
                "quiet_hours": {"start": "22:00", "end": "07:00"},
                "digest_mode": "daily",
                "weather_units": "metric",
                "weather_summary": True,
                "weather_location": "Home",
            },
        }

        page = render_user_detail("0.31.0", detail)

        self.assertIn("Mira &lt;Owner&gt;", page)
        self.assertIn("America/Vancouver", page)
        self.assertIn("Cheerful", page)
        self.assertIn("mon, wed, fri", page)
        self.assertIn("22:00–07:00", page)
        self.assertIn("Daily", page)
        self.assertIn("Enabled", page)
        self.assertNotIn("chat_id", page)

    def test_renders_safe_deployment_configuration(self):
        config = DashboardConfig(
            True,
            8,
            "amazon.titan-text-lite-v1",
            15,
            30,
            12,
            True,
        )

        page = render_config("0.31.0", config)

        self.assertIn("Configuration", page)
        self.assertIn("Enabled", page)
        self.assertIn("8 requests per week", page)
        self.assertIn("amazon.titan-text-lite-v1", page)
        self.assertIn("15 per minute", page)
        self.assertIn("Deployment managed", page)
        self.assertNotIn("ADMIN_API_TOKEN", page)
        self.assertNotIn("QUEUE_URL", page)
        self.assertIn("90 days", page)
        self.assertIn("14 days", page)
        self.assertIn("100 messages", page)
        self.assertIn("1000 messages", page)
        self.assertIn("100 items", page)
        self.assertIn("weather_calls=500", page)
        self.assertIn("queued_messages=5000", page)
        self.assertIn("friendly, brief, cheerful", page)
        self.assertIn("name, weekday, date", page)
        self.assertIn("information_requests=off", page)
        self.assertIn("greeting_previews=on", page)

    def test_renders_delivery_status_and_confirmed_redrive_form(self):
        page = render_delivery(
            "0.31.0", DeliveryQueueSummary(12, 3, 2)
        )

        self.assertIn('data-metric="pending">12<', page)
        self.assertIn('data-metric="failed">2<', page)
        self.assertIn('action="/admin/dashboard/delivery/redrive"', page)
        self.assertIn('name="confirm"', page)
        self.assertIn('name="rate"', page)
        self.assertIn('max="500"', page)
        self.assertIn('for="redrive-rate"', page)
        self.assertIn('aria-describedby="redrive-help"', page)
        self.assertIn(
            '<a href="/admin/dashboard/delivery" aria-current="page">Delivery</a>',
            page,
        )

    def test_renders_escaped_audit_history_and_next_page(self):
        record = AuditRecord(
            "audit-1",
            datetime(2025, 12, 11, 20, 0, tzinfo=timezone.utc),
            "configuration",
            "flags_<loaded>",
            "deployment",
            "request-1",
            ("greeting_previews",),
        )

        page = render_audit(
            "0.35.0",
            AuditPage((record,), "next-token"),
            AuditQuery(category="configuration", limit=10),
        )

        self.assertIn("Audit history", page)
        self.assertIn("flags_&lt;loaded&gt;", page)
        self.assertNotIn("flags_<loaded>", page)
        self.assertIn("greeting_previews", page)
        self.assertIn("cursor=next-token", page)
        self.assertIn('aria-label="Audit results"', page)
        self.assertIn('<th scope="col">Time</th>', page)

    def test_escapes_delivery_action_feedback(self):
        page = render_delivery(
            "0.31.0",
            DeliveryQueueSummary(0, 0, 0),
            "Task <started>",
        )

        self.assertIn("Task &lt;started&gt;", page)
        self.assertIn('role="status" aria-live="polite"', page)
        self.assertNotIn("Task <started>", page)


if __name__ == "__main__":
    unittest.main()
