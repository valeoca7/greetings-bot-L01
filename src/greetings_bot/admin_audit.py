from datetime import datetime
from typing import Dict, Mapping, Optional

from greetings_bot.configuration_audit import AuditQuery, AuditRecord


def parse_audit_query(values: Mapping[str, str]) -> AuditQuery:
    allowed = {"category", "since", "until", "limit", "cursor"}
    if set(values) - allowed:
        raise ValueError("unknown audit query parameter")
    try:
        limit = int(values.get("limit", "25"))
    except ValueError as error:
        raise ValueError("audit limit must be an integer") from error
    return AuditQuery(
        category=values.get("category") or None,
        since=_optional_time(values.get("since")),
        until=_optional_time(values.get("until")),
        limit=limit,
        after_id=values.get("cursor") or None,
    )


def audit_record_data(record: AuditRecord) -> Dict[str, object]:
    return {
        "id": record.id,
        "occurred_at": record.occurred_at.isoformat(),
        "category": record.category,
        "action": record.action,
        "source": record.source,
        "request_id": record.request_id,
        "changed_keys": list(record.changed_keys),
    }


def _optional_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("audit time must use ISO 8601") from error
    if parsed.tzinfo is None:
        raise ValueError("audit time must include a timezone")
    return parsed
