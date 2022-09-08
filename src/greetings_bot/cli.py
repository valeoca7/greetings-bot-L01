import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional, Sequence

from greetings_bot.runtime import process_payload
from greetings_bot.clock import FixedClock
from greetings_bot.scheduler import GreetingDispatcher
from greetings_bot.settings import Settings
from greetings_bot.telegram import reply_batch
from greetings_bot.update_parser import UpdateParseError
from greetings_bot.user_store import FileUserRepository, UserStoreError


def main(
    environ: Optional[Mapping[str, str]] = None,
    args: Optional[Sequence[str]] = None,
) -> int:
    settings = Settings.from_env(environ)
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--update", type=Path)
    action.add_argument("--dispatch-at")
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
    if options.dispatch_at is not None:
        try:
            users = FileUserRepository(settings.user_store_path)
            current_time = datetime.fromisoformat(options.dispatch_at)
            replies = GreetingDispatcher(users, FixedClock(current_time)).dispatch()
        except (ValueError, UserStoreError):
            print("error: unable to dispatch greetings", file=sys.stderr)
            return 1
        print(json.dumps(reply_batch(replies)))
        return 0
    print("greetings-bot is configured")
    return 0
