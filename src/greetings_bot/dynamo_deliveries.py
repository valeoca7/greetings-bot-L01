from typing import Dict

from greetings_bot.deliveries import Delivery
from greetings_bot.dynamo_users import DynamoTable


def delivery_key(delivery: Delivery) -> Dict[str, object]:
    return {
        "pk": "USER#{}".format(delivery.telegram_id),
        "sk": "DELIVERY#{}".format(delivery.day.isoformat()),
    }


class DynamoDeliveryLedger:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def contains(self, delivery: Delivery) -> bool:
        result = self.table.get_item(Key=delivery_key(delivery))
        return "Item" in result
