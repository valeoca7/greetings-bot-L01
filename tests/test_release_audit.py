import tempfile
import unittest
from pathlib import Path

from scripts.release_audit import audit_repository


class ReleaseAuditTest(unittest.TestCase):
    def test_current_repository_is_consistent(self):
        self.assertEqual(audit_repository(Path(".")), ())

    def test_reports_mismatched_versions_and_runtimes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/greetings_bot").mkdir(parents=True)
            (root / "setup.cfg").write_text(
                "[metadata]\nversion = next\n[options]\npython_requires = >=3.9\n"
            )
            (root / "src/greetings_bot/__init__.py").write_text(
                '__version__ = "0.1.0"\n'
            )
            (root / "template.yaml").write_text("Runtime: python3.9\n")
            (root / "Jenkinsfile").write_text("make check\n")

            errors = audit_repository(root)

        self.assertIn("package version is not a release version", errors)
        self.assertIn("package versions do not match", errors)
        self.assertIn("Python requirement is inconsistent", errors)
        self.assertIn("Lambda runtimes are inconsistent", errors)
        self.assertIn("pipeline is missing make test-scenarios", errors)


if __name__ == "__main__":
    unittest.main()
