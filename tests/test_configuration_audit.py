import unittest
from datetime import datetime, timezone

from greetings_bot.configuration_audit import (
    AuditQuery,
    AuditRecord,
    InMemoryAuditRepository,
    admin_action_record,
    configuration_snapshot_record,
    decode_audit_cursor,
)


class AuditRecordTest(unittest.TestCase):
    def test_keeps_attribution_without_configuration_values(self):
        record = AuditRecord(
            "audit-1",
            datetime(2025, 12, 3, 20, 0, tzinfo=timezone.utc),
            "configuration",
            "flags_loaded",
            "deployment",
            "request-1",
            ("greeting_previews", "weather_summaries"),
        )

        self.assertEqual(record.source, "deployment")
        self.assertEqual(record.changed_keys, ("greeting_previews", "weather_summaries"))
        self.assertFalse(hasattr(record, "values"))

    def test_rejects_private_or_unsorted_configuration_keys(self):
        for keys in (
            ("admin_api_token",),
            ("weather_summaries", "greeting_previews"),
        ):
            with self.subTest(keys=keys):
                with self.assertRaises(ValueError):
                    AuditRecord(
                        "audit-1",
                        datetime.now(timezone.utc),
                        "configuration",
                        "flags_loaded",
                        "runtime",
                        "request-1",
                        keys,
                    )

    def test_requires_aware_time_and_known_attribution(self):
        with self.assertRaises(ValueError):
            AuditRecord(
                "audit-1",
                datetime(2025, 12, 3, 20, 0),
                "configuration",
                "flags_loaded",
                "runtime",
                "request-1",
            )

    def test_builds_safe_configuration_and_action_records(self):
        now = datetime(2025, 12, 15, 20, 0, tzinfo=timezone.utc)

        configuration = configuration_snapshot_record(
            now,
            "startup",
            ("weather_summaries", "greeting_previews"),
        )
        action = admin_action_record(
            "delivery_redrive", "dashboard", now, "request-1"
        )

        self.assertEqual(
            configuration.changed_keys,
            ("greeting_previews", "weather_summaries"),
        )
        self.assertEqual(action.category, "admin_action")
        self.assertEqual(action.source, "dashboard")
        self.assertNotEqual(configuration.id, action.id)


class AuditQueryTest(unittest.TestCase):
    def test_accepts_a_bounded_time_filter(self):
        query = AuditQuery(
            "configuration",
            datetime(2025, 12, 1, tzinfo=timezone.utc),
            datetime(2025, 12, 4, tzinfo=timezone.utc),
            50,
        )

        self.assertEqual(query.limit, 50)

    def test_rejects_invalid_filters(self):
        with self.assertRaises(ValueError):
            AuditQuery(category="secrets")
        with self.assertRaises(ValueError):
            AuditQuery(limit=101)


class InMemoryAuditRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryAuditRepository()
        for record_id, hour, category in (
            ("a", 18, "configuration"),
            ("b", 20, "admin_action"),
            ("c", 20, "configuration"),
        ):
            self.repository.save(
                AuditRecord(
                    record_id,
                    datetime(2025, 12, 4, hour, tzinfo=timezone.utc),
                    category,
                    "changed",
                    "runtime",
                    "request-" + record_id,
                )
            )

    def test_returns_newest_records_with_stable_tie_breaking(self):
        page = self.repository.query(AuditQuery(limit=2))

        self.assertEqual([record.id for record in page.records], ["c", "b"])
        self.assertIn("#b", decode_audit_cursor(page.next_cursor))

    def test_filters_and_continues_after_a_cursor(self):
        first = self.repository.query(AuditQuery("configuration", limit=1))
        second = self.repository.query(
            AuditQuery("configuration", limit=1, after_id=first.next_cursor)
        )

        self.assertEqual([record.id for record in first.records], ["c"])
        self.assertEqual([record.id for record in second.records], ["a"])
        self.assertIsNone(second.next_cursor)

    def test_rejects_a_cursor_outside_the_filtered_result(self):
        with self.assertRaises(ValueError):
            self.repository.query(AuditQuery("configuration", after_id="bad"))


if __name__ == "__main__":
    unittest.main()
