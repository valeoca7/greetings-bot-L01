import argparse
import json
import sys
from pathlib import Path
from typing import Mapping, Optional, Sequence

from greetings_bot.runtime import process_payload
from greetings_bot.settings import Settings
from greetings_bot.update_parser import UpdateParseError


def main(
    environ: Optional[Mapping[str, str]] = None,
    args: Optional[Sequence[str]] = None,
) -> int:
    Settings.from_env(environ)
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", type=Path)
    options = parser.parse_args(args)
    if options.update is not None:
        try:
            payload = json.loads(options.update.read_text())
            reply = process_payload(payload)
        except (OSError, json.JSONDecodeError, UpdateParseError):
            print("error: unable to process update", file=sys.stderr)
            return 1
        if reply is not None:
            print(json.dumps(reply))
        return 0
    print("greetings-bot is configured")
    return 0
