import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.check_archive import check_archive


class SourceArchiveTest(unittest.TestCase):
    def test_accepts_a_versioned_source_archive(self):
        path = self._archive()

        check_archive(path)

    def test_rejects_private_paths_and_version_mismatches(self):
        with self.subTest(problem="private path"):
            with self.assertRaisesRegex(ValueError, "private build path"):
                check_archive(self._archive({".agents/SUMMARY.md": "private"}))
        with self.subTest(problem="version mismatch"):
            with self.assertRaisesRegex(ValueError, "versions do not match"):
                check_archive(
                    self._archive(
                        {"src/greetings_bot/__init__.py": '__version__ = "9.9.9"\n'}
                    )
                )

    def _archive(self, changes=None):
        files = {
            "README.md": "# Greetings Bot\n",
            "setup.cfg": "[metadata]\nversion = 0.43.0\n",
            "template.yaml": "Resources: {}\n",
            "src/greetings_bot/__init__.py": '__version__ = "0.43.0"\n',
        }
        files.update(changes or {})
        temporary = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with tarfile.open(path, "w:gz") as archive:
            for name, text in files.items():
                payload = text.encode("utf-8")
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
        self.addCleanup(path.unlink)
        return path


if __name__ == "__main__":
    unittest.main()
