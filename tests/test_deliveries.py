import unittest
from datetime import date

from greetings_bot.deliveries import Delivery


class DeliveryTest(unittest.TestCase):
    def test_keeps_user_and_day(self):
        delivery = Delivery(telegram_id=42, day=date(2022, 8, 27))

        self.assertEqual(42, delivery.telegram_id)
        self.assertEqual(date(2022, 8, 27), delivery.day)


if __name__ == "__main__":
    unittest.main()
