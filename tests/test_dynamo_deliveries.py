import unittest
from datetime import date

from greetings_bot.deliveries import Delivery
from greetings_bot.dynamo_deliveries import DynamoDeliveryLedger, delivery_key


class FakeTable:
    def __init__(self):
        self.items = {}

    def get_item(self, *, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {} if item is None else {"Item": item}

    def put_item(self, *, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}


class DeliveryKeyTest(unittest.TestCase):
    def test_includes_user_and_local_day(self):
        key = delivery_key(Delivery(42, date(2023, 1, 16)))

        self.assertEqual(
            key,
            {"pk": "USER#42", "sk": "DELIVERY#2023-01-16"},
        )


class DynamoDeliveryLedgerTest(unittest.TestCase):
    def test_finds_existing_delivery(self):
        table = FakeTable()
        delivery = Delivery(42, date(2023, 1, 16))
        table.items[("USER#42", "DELIVERY#2023-01-16")] = delivery_key(delivery)

        self.assertTrue(DynamoDeliveryLedger(table).contains(delivery))

    def test_reports_missing_delivery(self):
        ledger = DynamoDeliveryLedger(FakeTable())

        self.assertFalse(ledger.contains(Delivery(42, date(2023, 1, 16))))

    def test_records_delivery(self):
        table = FakeTable()
        ledger = DynamoDeliveryLedger(table)
        delivery = Delivery(42, date(2023, 1, 16))

        ledger.record(delivery)

        self.assertTrue(ledger.contains(delivery))
        self.assertEqual(
            table.items[("USER#42", "DELIVERY#2023-01-16")]["entity"],
            "delivery",
        )


if __name__ == "__main__":
    unittest.main()
