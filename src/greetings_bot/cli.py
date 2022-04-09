import argparse
import json
from pathlib import Path
from typing import Mapping, Optional, Sequence

from greetings_bot.runtime import process_payload
from greetings_bot.settings import Settings


def main(
    environ: Optional[Mapping[str, str]] = None,
    args: Optional[Sequence[str]] = None,
) -> None:
    Settings.from_env(environ)
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", type=Path)
    options = parser.parse_args(args)
    if options.update is not None:
        payload = json.loads(options.update.read_text())
        reply = process_payload(payload)
        if reply is not None:
            print(json.dumps(reply))
        return
    print("greetings-bot is configured")
