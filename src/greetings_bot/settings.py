import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    user_store_path: Path = Path("data/users.json")

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "Settings":
        values = os.environ if environ is None else environ
        token = values.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise SettingsError("TELEGRAM_BOT_TOKEN is required")
        store_path = Path(values.get("USER_STORE_PATH", "data/users.json"))
        return cls(telegram_token=token, user_store_path=store_path)
