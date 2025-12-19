from datetime import datetime, timedelta, timezone
from typing import Dict, Mapping

from greetings_bot.configuration_audit import (
    AuditPage,
    AuditQuery,
    AuditRecord,
    audit_sort_key,
    decode_audit_cursor,
    encode_audit_cursor,
)
from greetings_bot.dynamo_users import DynamoTable


def audit_item(
    record: AuditRecord, partition: str = "AUDIT", retention_days: int = 180
) -> Dict[str, object]:
    return {
        "pk": partition,
        "sk": audit_sort_key(record),
        "entity": "configuration_audit",
        "audit_id": record.id,
        "occurred_at": record.occurred_at.isoformat(),
        "category": record.category,
        "action": record.action,
        "source": record.source,
        "request_id": record.request_id,
        "changed_keys": list(record.changed_keys),
        "expires_at": int(
            (record.occurred_at + timedelta(days=retention_days)).timestamp()
        ),
    }


def audit_record_from_item(item: Mapping[str, object]) -> AuditRecord:
    changed_keys = item.get("changed_keys", [])
    if not isinstance(changed_keys, list):
        raise ValueError("invalid audit changed keys")
    return AuditRecord(
        str(item["audit_id"]),
        datetime.fromisoformat(str(item["occurred_at"])),
        str(item["category"]),
        str(item["action"]),
        str(item["source"]),
        str(item["request_id"]),
        tuple(str(key) for key in changed_keys),
    )


class DynamoAuditRepository:
    def __init__(self, table: DynamoTable, retention_days: int = 180) -> None:
        if retention_days < 1:
            raise ValueError("audit retention must be positive")
        self.table = table
        self.retention_days = retention_days

    def save(self, record: AuditRecord) -> None:
        for partition in ("AUDIT", "AUDIT#{}".format(record.category)):
            self.table.put_item(
                Item=audit_item(record, partition, self.retention_days)
            )

    def query(self, query: AuditQuery) -> AuditPage:
        partition = "AUDIT"
        if query.category is not None:
            partition = "AUDIT#{}".format(query.category)
        values = {":pk": partition}
        condition = "#pk = :pk"
        if query.since is not None:
            values[":since"] = _time_prefix(query.since)
            condition += " AND #sk >= :since"
        if query.until is not None:
            values[":until"] = _time_ceiling(query.until)
            condition += " AND #sk <= :until"
        arguments = {
            "KeyConditionExpression": condition,
            "ExpressionAttributeNames": {"#pk": "pk", "#sk": "sk"},
            "ExpressionAttributeValues": values,
            "ScanIndexForward": False,
            "Limit": query.limit + 1,
        }
        if query.after_id is not None:
            arguments["ExclusiveStartKey"] = {
                "pk": partition,
                "sk": decode_audit_cursor(query.after_id),
            }
        result = self.table.query(**arguments)
        items = result.get("Items", [])
        records = tuple(
            audit_record_from_item(item) for item in items[: query.limit]
        )
        next_cursor = (
            encode_audit_cursor(records[-1])
            if len(items) > query.limit and records
            else None
        )
        return AuditPage(records, next_cursor)


def _time_prefix(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat() + "#"


def _time_ceiling(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat() + "#\uffff"
