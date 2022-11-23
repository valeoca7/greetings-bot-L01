from typing import Dict

from greetings_bot.users import User, user_to_dict


def user_key(telegram_id: int) -> Dict[str, object]:
    return {
        "pk": "USER#{}".format(telegram_id),
        "sk": "PROFILE",
    }


def user_item(user: User) -> Dict[str, object]:
    item = user_to_dict(user)
    item.update(user_key(user.telegram_id))
    item["entity"] = "user"
    return item
