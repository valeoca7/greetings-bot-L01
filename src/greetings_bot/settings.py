import os
from dataclasses import dataclass
from typing import Mapping, Optional


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    telegram_token: str

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "Settings":
        values = os.environ if environ is None else environ
        token = values.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise SettingsError("TELEGRAM_BOT_TOKEN is required")
        return cls(telegram_token=token)
