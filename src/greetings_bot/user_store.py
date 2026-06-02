import json
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

from greetings_bot.users import User, user_from_dict, user_to_dict


class UserStoreError(ValueError):
    pass


class FileUserRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._users: Dict[int, User] = {}
        if self.path.exists():
            try:
                values = json.loads(self.path.read_text())
                self._users = {
                    user.telegram_id: user
                    for user in (user_from_dict(item) for item in values)
                }
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise UserStoreError("invalid user store") from error

    def save(self, user: User) -> None:
        self._users[user.telegram_id] = user
        self._write()

    def delete(self, telegram_id: int) -> bool:
        if telegram_id not in self._users:
            return False
        del self._users[telegram_id]
        self._write()
        return True

    def _write(self) -> None:
        values = [
            user_to_dict(self._users[telegram_id])
            for telegram_id in sorted(self._users)
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary_path.write_text(json.dumps(values, indent=2) + "\n")
        temporary_path.replace(self.path)

    def get(self, telegram_id: int) -> Optional[User]:
        return self._users.get(telegram_id)

    def count(self) -> int:
        return len(self._users)

    def all(self) -> Sequence[User]:
        return [self._users[user_id] for user_id in sorted(self._users)]

    def iter_all(self, page_size: int = 100) -> Iterable[User]:
        if page_size < 1:
            raise ValueError("page size must be positive")
        for user_id in sorted(self._users):
            yield self._users[user_id]
