import unittest

from greetings_bot.dynamo_users import user_item, user_key
from greetings_bot.users import User


class UserKeyTest(unittest.TestCase):
    def test_builds_user_profile_key(self):
        self.assertEqual(
            user_key(42),
            {"pk": "USER#42", "sk": "PROFILE"},
        )

    def test_maps_user_to_an_item(self):
        item = user_item(User(42, 84, "Mira"))

        self.assertEqual(item["pk"], "USER#42")
        self.assertEqual(item["sk"], "PROFILE")
        self.assertEqual(item["entity"], "user")
        self.assertEqual(item["first_name"], "Mira")


if __name__ == "__main__":
    unittest.main()
