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
        self._put(delivery)

    def claim(self, delivery: Delivery) -> bool:
        try:
            self._put(delivery, "attribute_not_exists(pk)")
        except Exception as error:
            response = getattr(error, "response", {})
            code = response.get("Error", {}).get("Code")
            if code == "ConditionalCheckFailedException":
                return False
            raise
        return True

    def _put(self, delivery: Delivery, condition: str = None) -> None:
        item = delivery_key(delivery)
        item["entity"] = "delivery"
        expires = datetime.combine(
            delivery.day + timedelta(days=self.retention_days),
            time.min,
            timezone.utc,
        )
        item["expires_at"] = int(expires.timestamp())
        arguments = {"Item": item}
        if condition is not None:
            arguments["ConditionExpression"] = condition
        self.table.put_item(**arguments)
