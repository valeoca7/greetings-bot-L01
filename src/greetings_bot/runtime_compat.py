import sys
from typing import Tuple


MINIMUM_PYTHON = (3, 11)


def require_supported_python(version: Tuple[int, int]) -> None:
    if version < MINIMUM_PYTHON:
        raise RuntimeError("greetings-bot requires Python 3.11 or newer")


def main() -> None:
    require_supported_python((sys.version_info.major, sys.version_info.minor))


if __name__ == "__main__":
    main()
