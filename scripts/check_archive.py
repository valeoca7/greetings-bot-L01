import argparse
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from configparser import ConfigParser
from pathlib import Path


REQUIRED_FILES = (
    "README.md",
    "setup.cfg",
    "setup.py",
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
    _check_clean_import(path, package_version.group(1))


def _read_text(archive: tarfile.TarFile, name: str) -> str:
    member = archive.extractfile(name)
    if member is None:
        raise ValueError("source archive member is unreadable")
    return member.read().decode("utf-8")


def _check_clean_import(path: Path, expected_version: str) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with tarfile.open(path, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile() or not member.name.startswith(
                    "src/greetings_bot/"
                ):
                    continue
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError("source archive member is unreadable")
                destination = root / member.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read())
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(root / "src")
        command = (
            "import greetings_bot; "
            "assert greetings_bot.__version__ == {!r}".format(expected_version)
        )
        try:
            subprocess.run(
                [sys.executable, "-c", command],
                cwd=root,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as error:
            raise ValueError("source archive cannot be imported") from error


def main() -> None:
    parser = argparse.ArgumentParser(description="verify the tracked source archive")
    parser.add_argument("archive", type=Path)
    arguments = parser.parse_args()
    check_archive(arguments.archive)


if __name__ == "__main__":
    main()
