from configparser import ConfigParser
import unittest

from greetings_bot import __version__


class PackageTest(unittest.TestCase):
    def test_has_package_version(self):
        self.assertEqual(__version__, "0.47.2")

    def test_declares_the_supported_python_range(self):
        config = ConfigParser()
        config.read("setup.cfg")

        self.assertEqual(config["options"]["python_requires"], ">=3.11")
        classifiers = config["metadata"]["classifiers"]
        for version in ("3.11", "3.12", "3.13"):
            self.assertIn("Python :: {}".format(version), classifiers)


if __name__ == "__main__":
    unittest.main()
