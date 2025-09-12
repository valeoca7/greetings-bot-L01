from datetime import datetime, time, timedelta, timezone
from typing import Dict

from greetings_bot.deliveries import Delivery
from greetings_bot.dynamo_users import DynamoTable


def delivery_key(delivery: Delivery) -> Dict[str, object]:
    return {
        "pk": "USER#{}".format(delivery.telegram_id),
        "sk": "DELIVERY#{}".format(delivery.day.isoformat()),
    }


class DynamoDeliveryLedger:
    def __init__(self, table: DynamoTable, retention_days: int = 90) -> None:
        self.table = table
        self.retention_days = retention_days

    def contains(self, delivery: Delivery) -> bool:
        result = self.table.get_item(Key=delivery_key(delivery))
        return "Item" in result

    def record(self, delivery: Delivery) -> None:
        item = delivery_key(delivery)
        item["entity"] = "delivery"
        expires = datetime.combine(
            delivery.day + timedelta(days=self.retention_days),
            time.min,
            timezone.utc,
        )
        item["expires_at"] = int(expires.timestamp())
        self.table.put_item(Item=item)
