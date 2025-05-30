import unittest

from greetings_bot.admin_dashboard import DashboardSnapshot, render_dashboard


class AdminDashboardTest(unittest.TestCase):
    def test_renders_a_semantic_dashboard_shell(self):
        page = render_dashboard("0.30.0")

        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("<title>Greetings Bot Admin</title>", page)
        self.assertIn('<meta name="viewport"', page)
        self.assertIn("<nav", page)
        self.assertIn("<main", page)
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


if __name__ == "__main__":
    unittest.main()
