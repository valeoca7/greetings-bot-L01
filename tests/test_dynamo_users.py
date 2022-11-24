import unittest

from greetings_bot.dynamo_users import user_from_item, user_item, user_key
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

    def test_restores_user_from_an_item(self):
        original = User(42, 84, "Mira", timezone="America/Vancouver")

        restored = user_from_item(user_item(original))

        self.assertEqual(restored, original)


if __name__ == "__main__":
    unittest.main()
