from datetime import timedelta
from typing import Dict, Mapping

from greetings_bot.dynamo_users import DynamoTable
from greetings_bot.information_quota import (
    InformationQuotaError,
    QuotaDecision,
    weekly_window,
)


def information_quota_key(telegram_id: int, week: str) -> Dict[str, object]:
    return {
        "pk": "USER#{}".format(telegram_id),
        "sk": "INFO_QUOTA#{}".format(week),
    }


class DynamoInformationQuota:
    def __init__(self, table: DynamoTable) -> None:
        self.table = table

    def consume(self, telegram_id, current_time, limit) -> QuotaDecision:
        if limit < 1:
            raise ValueError("weekly information limit must be positive")
        window = weekly_window(current_time)
        values = {
            ":entity": "information_quota",
            ":zero": 0,
            ":one": 1,
            ":limit": limit,
            ":expires_at": int(
                (window.resets_at + timedelta(days=7)).timestamp()
            ),
        }
        try:
            response = self.table.update_item(
                Key=information_quota_key(telegram_id, window.key),
                UpdateExpression=(
                    "SET #entity = if_not_exists(#entity, :entity), "
                    "#used = if_not_exists(#used, :zero) + :one, "
                    "#expires_at = :expires_at"
                ),
                ConditionExpression=(
                    "attribute_not_exists(#used) OR #used < :limit"
                ),
                ExpressionAttributeNames={
                    "#entity": "entity",
                    "#used": "used",
                    "#expires_at": "expires_at",
                },
                ExpressionAttributeValues=values,
                ReturnValues="ALL_NEW",
            )
        except Exception as error:
            if _is_limit_condition(error):
                return QuotaDecision(False, 0, window.resets_at)
            raise InformationQuotaError("quota storage unavailable") from error
        used = int(response["Attributes"]["used"])
        return QuotaDecision(True, max(0, limit - used), window.resets_at)


def _is_limit_condition(error: Exception) -> bool:
    response = getattr(error, "response", None)
    if not isinstance(response, Mapping):
        return False
    details = response.get("Error")
    return isinstance(details, Mapping) and details.get("Code") == (
        "ConditionalCheckFailedException"
    )
