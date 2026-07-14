import unittest
from html.parser import HTMLParser

from greetings_bot.admin_config import DashboardConfig
from greetings_bot.admin_dashboard import (
    render_config,
    render_dashboard,
    render_delivery,
    render_user_list,
)
from greetings_bot.admin_delivery import DeliveryQueueSummary
from greetings_bot.admin_users import AdminUserPage, AdminUserQuery


class MarkupAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.duplicate_ids = set()
        self.label_targets = []
        self.main_count = 0
        self.h1_count = 0

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        if tag == "label" and values.get("for"):
            self.label_targets.append(values["for"])
        if tag == "main":
            self.main_count += 1
        if tag == "h1":
            self.h1_count += 1


class AdminAccessibilityTest(unittest.TestCase):
    def test_pages_have_one_main_heading_and_unique_control_labels(self):
        pages = (
            render_dashboard("0.42.0"),
            render_user_list(
                "0.42.0",
                AdminUserPage((), False, None),
                AdminUserQuery(),
            ),
            render_delivery("0.42.0", DeliveryQueueSummary(1, 0, 0)),
            render_config(
                "0.42.0",
                DashboardConfig(False, 5, "local-model", 20, 60, 24, True),
            ),
        )

        for page in pages:
            with self.subTest(title=page.split("<title>", 1)[1].split("</title>", 1)[0]):
                audit = MarkupAudit()
                audit.feed(page)
                self.assertEqual(audit.main_count, 1)
                self.assertEqual(audit.h1_count, 1)
                self.assertEqual(audit.duplicate_ids, set())
                self.assertTrue(set(audit.label_targets).issubset(audit.ids))
                self.assertIn("main-content", audit.ids)


if __name__ == "__main__":
    unittest.main()
