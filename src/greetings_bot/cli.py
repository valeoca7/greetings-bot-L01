from typing import Mapping, Optional

from greetings_bot.settings import Settings


def main(environ: Optional[Mapping[str, str]] = None) -> None:
    Settings.from_env(environ)
    print("greetings-bot is configured")
