from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Note:
    id: str
    owner_id: int
    text: str
    created_at: datetime
