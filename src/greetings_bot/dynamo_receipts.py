from typing import Dict

from greetings_bot.dynamo_users import DynamoTable


def receipt_key(delivery_id: str) -> Dict[str, object]:
    return {"pk": "DELIVERY#{}".format(delivery_id), "sk": "RECEIPT"}


class DynamoDeliveryReceiptLedger:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def contains(self, delivery_id: str) -> bool:
        return "Item" in self.table.get_item(Key=receipt_key(delivery_id))

    def record(self, delivery_id: str) -> None:
        item = receipt_key(delivery_id)
        item["entity"] = "delivery_receipt"
        self.table.put_item(Item=item)
