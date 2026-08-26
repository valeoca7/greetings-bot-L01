import argparse
import re
import tarfile
from configparser import ConfigParser
from pathlib import Path


REQUIRED_FILES = (
    "README.md",
    "setup.cfg",
    "template.yaml",
    "src/greetings_bot/__init__.py",
)
PRIVATE_PREFIXES = (".agents/", ".git/", "dist/")


def check_archive(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        names = set(archive.getnames())
        missing = [name for name in REQUIRED_FILES if name not in names]
        if missing:
            raise ValueError("source archive is missing {}".format(missing[0]))
        if any(name.startswith(PRIVATE_PREFIXES) for name in names):
            raise ValueError("source archive contains a private build path")
        setup_text = _read_text(archive, "setup.cfg")
        package_text = _read_text(archive, "src/greetings_bot/__init__.py")
    config = ConfigParser()
    config.read_string(setup_text)
    package_version = re.search(r'^__version__ = "([^"]+)"$', package_text)
    if package_version is None:
        raise ValueError("package version is missing")
    if package_version.group(1) != config["metadata"]["version"]:
        raise ValueError("package versions do not match")


def _read_text(archive: tarfile.TarFile, name: str) -> str:
    member = archive.extractfile(name)
    if member is None:
        raise ValueError("source archive member is unreadable")
    return member.read().decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="verify the tracked source archive")
    parser.add_argument("archive", type=Path)
    arguments = parser.parse_args()
    check_archive(arguments.archive)


if __name__ == "__main__":
    main()
