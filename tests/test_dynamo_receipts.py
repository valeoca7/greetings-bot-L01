import unittest

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
        ledger = DynamoDeliveryReceiptLedger(FakeTable())

        self.assertFalse(ledger.contains("delivery-1"))
        ledger.record("delivery-1")

        self.assertTrue(ledger.contains("delivery-1"))
        self.assertEqual(
            receipt_key("delivery-1"),
            {"pk": "DELIVERY#delivery-1", "sk": "RECEIPT"},
        )


if __name__ == "__main__":
    unittest.main()
