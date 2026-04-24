import unittest

from greetings_bot import __version__


class PackageTest(unittest.TestCase):
    def test_has_package_version(self):
        self.assertEqual(__version__, "0.39.0")


if __name__ == "__main__":
    unittest.main()
