import unittest
from datetime import datetime, timezone

from greetings_bot.dynamo_information_quota import (
    DynamoInformationQuota,
    information_quota_key,
)
from greetings_bot.information_quota import InformationQuotaError


class ClientError(Exception):
    def __init__(self, code):
        self.response = {"Error": {"Code": code}}


class FakeTable:
    def __init__(self, used=1, error=None):
        self.used = used
        self.error = error

    def update_item(self, **request):
        self.request = request
        if self.error:
            raise self.error
        return {"Attributes": {"used": self.used}}


class InformationQuotaKeyTest(unittest.TestCase):
    def test_places_the_week_counter_beside_the_user(self):
        self.assertEqual(
            information_quota_key(42, "2024-W43"),
            {"pk": "USER#42", "sk": "INFO_QUOTA#2024-W43"},
        )


class DynamoInformationQuotaTest(unittest.TestCase):
    def setUp(self):
        self.current_time = datetime(
            2024, 10, 22, 20, 0, tzinfo=timezone.utc
        )

    def test_atomically_increments_a_week_counter(self):
        table = FakeTable(used=2)

        decision = DynamoInformationQuota(table).consume(
            42, self.current_time, 5
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.remaining, 3)
        self.assertEqual(
            table.request["Key"],
            {"pk": "USER#42", "sk": "INFO_QUOTA#2024-W43"},
        )
        self.assertIn("#used < :limit", table.request["ConditionExpression"])
        self.assertEqual(
            table.request["ExpressionAttributeValues"][":limit"], 5
        )
        self.assertEqual(table.request["ReturnValues"], "ALL_NEW")

    def test_returns_denied_for_a_failed_limit_condition(self):
        table = FakeTable(
            error=ClientError("ConditionalCheckFailedException")
        )

        decision = DynamoInformationQuota(table).consume(
            42, self.current_time, 5
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.remaining, 0)
        self.assertEqual(decision.resets_at.day, 28)

    def test_does_not_hide_other_database_errors(self):
        error = ClientError("ProvisionedThroughputExceededException")

        with self.assertRaises(InformationQuotaError) as raised:
            DynamoInformationQuota(FakeTable(error=error)).consume(
                42, self.current_time, 5
            )

        self.assertIs(raised.exception.__cause__, error)


if __name__ == "__main__":
    unittest.main()
