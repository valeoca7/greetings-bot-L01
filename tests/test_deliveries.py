import unittest
from datetime import date

from greetings_bot.deliveries import Delivery, InMemoryDeliveryLedger


class DeliveryTest(unittest.TestCase):
    def test_keeps_user_and_day(self):
        delivery = Delivery(telegram_id=42, day=date(2022, 8, 27))

        self.assertEqual(42, delivery.telegram_id)
        self.assertEqual(date(2022, 8, 27), delivery.day)

    def test_records_a_delivery_once(self):
        ledger = InMemoryDeliveryLedger()
        delivery = Delivery(telegram_id=42, day=date(2022, 8, 29))

        self.assertFalse(ledger.contains(delivery))
        ledger.record(delivery)
        ledger.record(delivery)

        self.assertTrue(ledger.contains(delivery))


if __name__ == "__main__":
    unittest.main()
