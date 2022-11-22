def user_key(telegram_id: int):
    return {
        "pk": "USER#{}".format(telegram_id),
        "sk": "PROFILE",
    }
