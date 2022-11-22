import unittest

from greetings_bot.dynamo_users import user_key


class UserKeyTest(unittest.TestCase):
    def test_builds_user_profile_key(self):
        self.assertEqual(
            user_key(42),
            {"pk": "USER#42", "sk": "PROFILE"},
        )


if __name__ == "__main__":
    unittest.main()
