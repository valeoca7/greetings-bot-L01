from typing import Dict

from greetings_bot.deliveries import Delivery


def delivery_key(delivery: Delivery) -> Dict[str, object]:
    return {
        "pk": "USER#{}".format(delivery.telegram_id),
        "sk": "DELIVERY#{}".format(delivery.day.isoformat()),
    }
