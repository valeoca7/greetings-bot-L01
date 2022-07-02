import json
from pathlib import Path
from typing import Dict, Optional

from greetings_bot.users import User, user_to_dict


class FileUserRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._users: Dict[int, User] = {}

    def save(self, user: User) -> None:
        self._users[user.telegram_id] = user
        values = [user_to_dict(item) for item in self._users.values()]
        self.path.write_text(json.dumps(values, indent=2) + "\n")

    def get(self, telegram_id: int) -> Optional[User]:
        return self._users.get(telegram_id)

    def count(self) -> int:
        return len(self._users)
