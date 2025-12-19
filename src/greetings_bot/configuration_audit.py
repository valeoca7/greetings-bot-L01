import base64
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, Protocol, Tuple


AUDIT_CATEGORIES = ("configuration", "admin_action")
AUDIT_SOURCES = ("deployment", "runtime", "dashboard")
PUBLIC_CONFIGURATION_KEYS = (
    "information_requests",
    "greeting_previews",
    "weather_summaries",
    "information_weekly_limit",
    "weather_max_calls",
    "weather_cache_minutes",
    "weather_stale_hours",
)


def audit_sort_key(record: "AuditRecord") -> str:
    stamp = record.occurred_at.astimezone(timezone.utc)
    return "{}#{}".format(stamp.isoformat(), record.id)


def encode_audit_cursor(record: "AuditRecord") -> str:
    return base64.urlsafe_b64encode(audit_sort_key(record).encode("utf-8")).decode(
        "ascii"
    )


def decode_audit_cursor(value: str) -> str:
    try:
        decoded = base64.urlsafe_b64decode(value.encode("ascii")).decode("utf-8")
    except (UnicodeError, ValueError) as error:
        raise ValueError("invalid audit cursor") from error
    if "#" not in decoded:
        raise ValueError("invalid audit cursor")
    return decoded


@dataclass(frozen=True)
class AuditRecord:
    id: str
    occurred_at: datetime
    category: str
    action: str
    source: str
    request_id: str
    changed_keys: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id or len(self.id) > 80:
            raise ValueError("invalid audit record id")
        if self.occurred_at.tzinfo is None:
            raise ValueError("audit time must include a timezone")
        if self.category not in AUDIT_CATEGORIES:
            raise ValueError("unknown audit category")
        if self.source not in AUDIT_SOURCES:
            raise ValueError("unknown audit source")
        if not self.action or len(self.action) > 80:
            raise ValueError("invalid audit action")
        if not self.request_id or len(self.request_id) > 128:
            raise ValueError("invalid audit request id")
        if tuple(sorted(set(self.changed_keys))) != self.changed_keys:
            raise ValueError("audit changed keys must be sorted and unique")
        if any(key not in PUBLIC_CONFIGURATION_KEYS for key in self.changed_keys):
            raise ValueError("private configuration key cannot be audited")


@dataclass(frozen=True)
class AuditQuery:
    category: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: int = 25
    after_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.category is not None and self.category not in AUDIT_CATEGORIES:
            raise ValueError("unknown audit category")
        if not 1 <= self.limit <= 100:
            raise ValueError("audit limit must be between 1 and 100")
        for value in (self.since, self.until):
            if value is not None and value.tzinfo is None:
                raise ValueError("audit query times must include a timezone")
        if self.since and self.until and self.since > self.until:
            raise ValueError("audit time range is reversed")
        if self.after_id is not None and not self.after_id:
            raise ValueError("audit cursor must not be blank")


@dataclass(frozen=True)
class AuditPage:
    records: Tuple[AuditRecord, ...]
    next_cursor: Optional[str]


class AuditRepository(Protocol):
    def save(self, record: AuditRecord) -> None:
        ...

    def query(self, query: AuditQuery) -> AuditPage:
        ...


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self.records: Dict[str, AuditRecord] = {}

    def save(self, record: AuditRecord) -> None:
        self.records[record.id] = record

    def query(self, query: AuditQuery) -> AuditPage:
        records = [
            record
            for record in self.records.values()
            if (query.category is None or record.category == query.category)
            and (query.since is None or record.occurred_at >= query.since)
            and (query.until is None or record.occurred_at <= query.until)
        ]
        records.sort(key=lambda record: (record.occurred_at, record.id), reverse=True)
        if query.after_id is not None:
            cursor_key = decode_audit_cursor(query.after_id)
            positions = [
                index
                for index, record in enumerate(records)
                if audit_sort_key(record) == cursor_key
            ]
            if not positions:
                raise ValueError("unknown audit cursor")
            records = records[positions[0] + 1 :]
        selected = tuple(records[: query.limit])
        next_cursor = (
            encode_audit_cursor(selected[-1])
            if len(records) > query.limit and selected
            else None
        )
        return AuditPage(selected, next_cursor)


def configuration_snapshot_record(
    occurred_at: datetime, request_id: str, keys: Tuple[str, ...]
) -> AuditRecord:
    return AuditRecord(
        _audit_id("configuration", request_id, "configuration_loaded"),
        occurred_at,
        "configuration",
        "configuration_loaded",
        "deployment",
        request_id,
        tuple(sorted(keys)),
    )


def admin_action_record(
    action: str, source: str, occurred_at: datetime, request_id: str
) -> AuditRecord:
    return AuditRecord(
        _audit_id("admin", request_id, action),
        occurred_at,
        "admin_action",
        action,
        source,
        request_id,
    )


def _audit_id(category: str, request_id: str, action: str) -> str:
    digest = hashlib.sha256(
        "{}:{}".format(request_id, action).encode("utf-8")
    ).hexdigest()[:20]
    return "{}-{}".format(category, digest)
