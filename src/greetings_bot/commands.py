from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Command:
    name: str
    arguments: Tuple[str, ...]


def parse_command(text: Optional[str]) -> Optional[Command]:
    if text is None or not text.startswith("/"):
        return None
    parts = text.split()
    name = parts[0][1:].split("@", 1)[0].lower()
    if not name:
        return None
    return Command(name=name, arguments=tuple(parts[1:]))
