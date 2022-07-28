import argparse
import json
import sys
from pathlib import Path
from typing import Mapping, Optional, Sequence

from greetings_bot.runtime import process_payload
from greetings_bot.settings import Settings
from greetings_bot.update_parser import UpdateParseError
from greetings_bot.user_store import FileUserRepository, UserStoreError


def main(
    environ: Optional[Mapping[str, str]] = None,
    args: Optional[Sequence[str]] = None,
) -> int:
    settings = Settings.from_env(environ)
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", type=Path)
    options = parser.parse_args(args)
    if options.update is not None:
        try:
            payload = json.loads(options.update.read_text())
            users = FileUserRepository(settings.user_store_path)
            reply = process_payload(payload, users)
        except (OSError, json.JSONDecodeError, UpdateParseError, UserStoreError):
            print("error: unable to process update", file=sys.stderr)
            return 1
        if reply is not None:
            print(json.dumps(reply))
        return 0
    print("greetings-bot is configured")
    return 0
