import unittest
from datetime import date

from greetings_bot.deliveries import Delivery
from greetings_bot.dynamo_deliveries import delivery_key


class DeliveryKeyTest(unittest.TestCase):
    def test_includes_user_and_local_day(self):
        key = delivery_key(Delivery(42, date(2023, 1, 16)))

        self.assertEqual(
            key,
            {"pk": "USER#42", "sk": "DELIVERY#2023-01-16"},
        )


if __name__ == "__main__":
    unittest.main()
