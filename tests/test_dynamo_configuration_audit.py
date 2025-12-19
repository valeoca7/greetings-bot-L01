import unittest
from datetime import datetime, timezone

from greetings_bot.configuration_audit import AuditQuery, AuditRecord
from greetings_bot.dynamo_configuration_audit import (
    DynamoAuditRepository,
    audit_item,
    audit_record_from_item,
)


class FakeTable:
    def __init__(self):
        self.items = []
        self.last_query = None

    def put_item(self, *, Item):
        self.items.append(dict(Item))
        return {}

    def query(self, **arguments):
        self.last_query = arguments
        partition = arguments["ExpressionAttributeValues"][":pk"]
        items = [item for item in self.items if item["pk"] == partition]
        items.sort(key=lambda item: item["sk"], reverse=True)
        start = arguments.get("ExclusiveStartKey")
        if start:
            positions = [
                index for index, item in enumerate(items) if item["sk"] == start["sk"]
            ]
            items = items[positions[0] + 1 :] if positions else []
        return {"Items": items[: arguments["Limit"]]}


def record(record_id, hour, category="configuration"):
    return AuditRecord(
        record_id,
        datetime(2025, 12, 8, hour, tzinfo=timezone.utc),
        category,
        "flags_loaded",
        "deployment",
        "request-" + record_id,
    )


class DynamoAuditMappingTest(unittest.TestCase):
    def test_round_trips_a_ttl_backed_record(self):
        original = record("audit-1", 20)

        item = audit_item(original)

        self.assertEqual(audit_record_from_item(item), original)
        self.assertGreater(item["expires_at"], int(original.occurred_at.timestamp()))
        self.assertNotIn("values", item)


class DynamoAuditRepositoryTest(unittest.TestCase):
    def test_saves_global_and_category_query_records(self):
        table = FakeTable()
        repository = DynamoAuditRepository(table)

        repository.save(record("audit-1", 20))

        self.assertEqual([item["pk"] for item in table.items], [
            "AUDIT", "AUDIT#configuration"
        ])

    def test_queries_newest_records_with_a_bounded_page(self):
        table = FakeTable()
        repository = DynamoAuditRepository(table)
        repository.save(record("a", 18))
        repository.save(record("b", 19))
        repository.save(record("c", 20))

        first = repository.query(AuditQuery("configuration", limit=2))
        second = repository.query(
            AuditQuery("configuration", limit=2, after_id=first.next_cursor)
        )

        self.assertEqual([item.id for item in first.records], ["c", "b"])
        self.assertEqual([item.id for item in second.records], ["a"])
        self.assertEqual(table.last_query["Limit"], 3)

    def test_rejects_non_positive_retention(self):
        with self.assertRaises(ValueError):
            DynamoAuditRepository(FakeTable(), retention_days=0)


if __name__ == "__main__":
    unittest.main()
