import base64
import binascii
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple

from greetings_bot.users import User


@dataclass(frozen=True)
class AdminUserQuery:
    term: str = ""
    status: str = "all"
    limit: int = 20
    after_id: Optional[int] = None


@dataclass(frozen=True)
class AdminUserPage:
    items: Tuple[Dict[str, object], ...]
    has_more: bool
    next_cursor: Optional[str]


def parse_user_query(params: Mapping[str, str]) -> AdminUserQuery:
    term = params.get("q", "").strip()
    if len(term) > 50:
        raise ValueError("user search must be 50 characters or shorter")
    status = params.get("status", "all").lower()
    if status not in ("all", "active", "disabled"):
        raise ValueError("user status must be all, active, or disabled")
    try:
        limit = int(params.get("limit", "20"))
    except ValueError as error:
        raise ValueError("user limit must be an integer") from error
    if not 1 <= limit <= 50:
        raise ValueError("user limit must be between 1 and 50")
    cursor = params.get("cursor")
    after_id = decode_user_cursor(cursor) if cursor else None
    return AdminUserQuery(term, status, limit, after_id)


def encode_user_cursor(telegram_id: int) -> str:
    value = "user:{}".format(telegram_id).encode("ascii")
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def decode_user_cursor(cursor: str) -> int:
    try:
        padding = "=" * (-len(cursor) % 4)
        value = base64.b64decode(
            cursor + padding, altchars=b"-_", validate=True
        ).decode("ascii")
        prefix, raw_id = value.split(":", 1)
        telegram_id = int(raw_id)
        if prefix != "user" or telegram_id < 1:
            raise ValueError
        return telegram_id
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise ValueError("invalid user cursor")


def search_users(
    users: Sequence[User], query: AdminUserQuery
) -> AdminUserPage:
    term = query.term.casefold()
    matches = []
    for user in users:
        if query.after_id is not None and user.telegram_id <= query.after_id:
            continue
        if query.status == "active" and not user.enabled:
            continue
        if query.status == "disabled" and user.enabled:
            continue
        if term and term not in user.first_name.casefold() and term != str(
            user.telegram_id
        ):
            continue
        matches.append(user)
    matches.sort(key=lambda user: user.telegram_id)
    selected = matches[: query.limit]
    items = tuple(
        {
            "id": user.telegram_id,
            "name": user.first_name,
            "status": "active" if user.enabled else "disabled",
            "timezone": user.timezone,
            "greeting_time": user.greeting_time,
        }
        for user in selected
    )
    has_more = len(matches) > query.limit
    next_cursor = (
        encode_user_cursor(selected[-1].telegram_id)
        if has_more and selected
        else None
    )
    return AdminUserPage(items, has_more, next_cursor)


def user_detail(user: User) -> Dict[str, object]:
    quiet_hours = None
    if user.quiet_start is not None and user.quiet_end is not None:
        quiet_hours = {"start": user.quiet_start, "end": user.quiet_end}
    preferences = {
        "locale": user.locale,
        "timezone": user.timezone,
        "greeting_time": user.greeting_time,
        "greeting_days": list(user.greeting_days),
        "quiet_hours": quiet_hours,
        "digest_mode": user.digest_mode,
        "weather_units": user.weather_units,
        "weather_summary": user.weather_summary,
        "weather_location": (
            user.weather_location.name
            if user.weather_location is not None
            else None
        ),
    }
    return {
        "id": user.telegram_id,
        "name": user.first_name,
        "status": "active" if user.enabled else "disabled",
        "preferences": preferences,
    }
