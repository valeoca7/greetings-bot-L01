import unittest

from greetings_bot import __version__


class PackageTest(unittest.TestCase):
    def test_has_initial_version(self):
        self.assertEqual(__version__, "0.0.1")


if __name__ == "__main__":
    unittest.main()
