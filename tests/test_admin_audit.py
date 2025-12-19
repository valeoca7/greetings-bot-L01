import unittest
from datetime import datetime, timezone

from greetings_bot.admin_audit import audit_record_data, parse_audit_query
from greetings_bot.configuration_audit import AuditRecord


class AdminAuditQueryTest(unittest.TestCase):
    def test_reads_bounded_filters_and_cursor(self):
        query = parse_audit_query(
            {
                "category": "configuration",
                "since": "2025-12-01T00:00:00Z",
                "until": "2025-12-09T00:00:00+00:00",
                "limit": "40",
                "cursor": "opaque",
            }
        )

        self.assertEqual(query.category, "configuration")
        self.assertEqual(query.limit, 40)
        self.assertEqual(query.after_id, "opaque")

    def test_rejects_unknown_or_invalid_filters(self):
        for values in (
            {"owner": "42"},
            {"limit": "all"},
            {"since": "yesterday"},
            {"since": "2025-12-01T00:00:00"},
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    parse_audit_query(values)


class AdminAuditDataTest(unittest.TestCase):
    def test_serializes_attribution_without_values(self):
        record = AuditRecord(
            "audit-1",
            datetime(2025, 12, 9, 20, 0, tzinfo=timezone.utc),
            "configuration",
            "flags_loaded",
            "deployment",
            "request-1",
            ("greeting_previews",),
        )

        data = audit_record_data(record)

        self.assertEqual(data["changed_keys"], ["greeting_previews"])
        self.assertNotIn("values", data)


if __name__ == "__main__":
    unittest.main()
