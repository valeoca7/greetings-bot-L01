import unittest

from greetings_bot.information_runtime import information_requests_enabled


class InformationRuntimeTest(unittest.TestCase):
    def test_information_requests_are_disabled_by_default(self):
        self.assertFalse(information_requests_enabled({}))

    def test_enables_information_requests_explicitly(self):
        self.assertTrue(
            information_requests_enabled({"INFO_REQUESTS_ENABLED": "true"})
        )

    def test_rejects_ambiguous_feature_flag(self):
        with self.assertRaises(ValueError):
            information_requests_enabled({"INFO_REQUESTS_ENABLED": "sometimes"})


if __name__ == "__main__":
    unittest.main()
