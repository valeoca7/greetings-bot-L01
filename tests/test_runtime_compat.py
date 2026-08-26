import unittest

from greetings_bot.runtime_compat import require_supported_python


class RuntimeCompatibilityTest(unittest.TestCase):
    def test_accepts_supported_python_versions(self):
        for version in ((3, 11), (3, 12), (3, 13), (3, 14)):
            with self.subTest(version=version):
                require_supported_python(version)

    def test_rejects_an_older_interpreter(self):
        with self.assertRaisesRegex(RuntimeError, "Python 3.11 or newer"):
            require_supported_python((3, 10))


if __name__ == "__main__":
    unittest.main()
