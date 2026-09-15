import argparse
import re
from configparser import ConfigParser
from pathlib import Path
from typing import Tuple


VERSION_PATTERN = re.compile(r"^0\.\d+\.\d+$")


def audit_repository(root: Path) -> Tuple[str, ...]:
    errors = []
    config = ConfigParser()
    config.read(root / "setup.cfg")
    metadata_version = config["metadata"].get("version", "")
    package_text = (root / "src/greetings_bot/__init__.py").read_text()
    package_match = re.search(r'^__version__ = "([^"]+)"$', package_text)
    package_version = package_match.group(1) if package_match else ""
    if not VERSION_PATTERN.fullmatch(metadata_version):
        errors.append("package version is not a release version")
    if package_version != metadata_version:
        errors.append("package versions do not match")
    if config["options"].get("python_requires") != ">=3.11":
        errors.append("Python requirement is inconsistent")
    template = (root / "template.yaml").read_text()
    if template.count("Runtime: python3.13") != 5:
        errors.append("Lambda runtimes are inconsistent")
    pipeline = (root / "Jenkinsfile").read_text()
    for command in ("make check", "make test-scenarios", "make check-package"):
        if command not in pipeline:
            errors.append("pipeline is missing {}".format(command))
    return tuple(errors)


def main() -> None:
    parser = argparse.ArgumentParser(description="audit release metadata")
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    arguments = parser.parse_args()
    errors = audit_repository(arguments.root)
    if errors:
        raise SystemExit("; ".join(errors))


if __name__ == "__main__":
    main()
