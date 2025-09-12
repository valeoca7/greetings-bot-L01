import unittest
from datetime import datetime, timedelta, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.dynamo_receipts import (
    DynamoDeliveryReceiptLedger,
    receipt_key,
)


class FakeTable:
    def __init__(self):
        self.items = {}

    def get_item(self, *, Key):
        item = self.items.get((Key["pk"], Key["sk"]))
        return {} if item is None else {"Item": item}

    def put_item(self, *, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)
        return {}


class DynamoDeliveryReceiptLedgerTest(unittest.TestCase):
    def test_records_delivery_id_once(self):
        table = FakeTable()
        now = datetime(2025, 9, 11, 3, 0, tzinfo=timezone.utc)
        ledger = DynamoDeliveryReceiptLedger(
            table, 7, FixedClock(now)
        )

        self.assertFalse(ledger.contains("delivery-1"))
        ledger.record("delivery-1")

        self.assertTrue(ledger.contains("delivery-1"))
        self.assertEqual(
            receipt_key("delivery-1"),
            {"pk": "DELIVERY#delivery-1", "sk": "RECEIPT"},
        )
        self.assertEqual(
            table.items[("DELIVERY#delivery-1", "RECEIPT")]["expires_at"],
            int((now + timedelta(days=7)).timestamp()),
        )


if __name__ == "__main__":
    unittest.main()
