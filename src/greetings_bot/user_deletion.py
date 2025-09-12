import hashlib
import hmac
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional


DeletionStatus = Literal["requested", "confirmed", "completed"]


@dataclass(frozen=True)
class DeletionRequest:
    telegram_id: int
    token_digest: str
    requested_at: datetime
    expires_at: datetime
    status: DeletionStatus = "requested"
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


def request_deletion(
    telegram_id: int,
    token: str,
    current_time: datetime,
    lifetime: timedelta = timedelta(minutes=30),
) -> DeletionRequest:
    current_time = _utc_time(current_time)
    if telegram_id < 1:
        raise ValueError("user id must be positive")
    if not 16 <= len(token) <= 200:
        raise ValueError("deletion token is invalid")
    if not timedelta(minutes=5) <= lifetime <= timedelta(hours=1):
        raise ValueError("deletion token lifetime is invalid")
    return DeletionRequest(
        telegram_id,
        _token_digest(token),
        current_time,
        current_time + lifetime,
    )


def confirm_deletion(
    request: DeletionRequest, token: str, current_time: datetime
) -> DeletionRequest:
    current_time = _utc_time(current_time)
    if request.status != "requested":
        raise ValueError("deletion request is not awaiting confirmation")
    if current_time >= request.expires_at:
        raise ValueError("deletion confirmation has expired")
    if not hmac.compare_digest(request.token_digest, _token_digest(token)):
        raise ValueError("deletion confirmation is invalid")
    return replace(
        request,
        status="confirmed",
        confirmed_at=current_time,
    )


def complete_deletion(
    request: DeletionRequest, current_time: datetime
) -> DeletionRequest:
    current_time = _utc_time(current_time)
    if request.status != "confirmed":
        raise ValueError("deletion request is not confirmed")
    return replace(
        request,
        status="completed",
        completed_at=current_time,
    )


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("deletion time must include a timezone")
    return value.astimezone(timezone.utc)
