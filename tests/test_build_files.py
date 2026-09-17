import unittest
from pathlib import Path


class BuildFilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.makefile = Path("Makefile").read_text()
        cls.jenkinsfile = Path("Jenkinsfile").read_text()

    def test_makefile_has_check_and_package_targets(self):
        self.assertIn("help:", self.makefile)
        self.assertIn(
            "check: check-runtime check-syntax test-unit check-template",
            self.makefile,
        )
        self.assertIn("greetings_bot.runtime_compat", self.makefile)
        self.assertIn("package:", self.makefile)
        self.assertIn("greetings-bot-src.tar.gz", self.makefile)
        self.assertIn("git archive", self.makefile)
        self.assertIn("check-package: package", self.makefile)
        self.assertIn("scripts/check_archive.py", self.makefile)

    def test_makefile_can_inspect_a_saved_replay(self):
        self.assertIn("replay-plan:", self.makefile)
        self.assertIn("greetings_bot.replay $(EVENT)", self.makefile)

    def test_build_can_run_bounded_offline_scenarios(self):
        self.assertIn("test-scenarios:", self.makefile)
        self.assertIn("tests.test_offline_scenarios", self.makefile)
        self.assertIn("tests.test_legacy_records", self.makefile)
        self.assertIn("sh 'make test-scenarios'", self.jenkinsfile)

    def test_build_has_one_complete_release_gate(self):
        self.assertIn(
            "check-release: check test-scenarios check-package audit-release",
            self.makefile,
        )
        self.assertIn("scripts/release_audit.py", self.makefile)
        self.assertIn("sh 'make audit-release'", self.jenkinsfile)

    def test_pipeline_runs_the_local_workflow(self):
        self.assertIn("sh 'make check'", self.jenkinsfile)
        self.assertIn("sh 'make check-package'", self.jenkinsfile)

    def test_pipeline_bounds_and_archives_builds(self):
        self.assertIn("disableConcurrentBuilds()", self.jenkinsfile)
        self.assertIn("timeout(time: 15", self.jenkinsfile)
        self.assertIn("archiveArtifacts", self.jenkinsfile)
        self.assertIn("fingerprint: true", self.jenkinsfile)


if __name__ == "__main__":
    unittest.main()
