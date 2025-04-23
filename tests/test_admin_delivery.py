import unittest

from greetings_bot.admin_delivery import (
    DeliveryAdminError,
    DeliveryQueueSummary,
    SqsDeliveryAdmin,
    delivery_admin_from_env,
)


class FakeSqsClient:
    def __init__(self):
        self.requests = []

    def get_queue_attributes(self, **request):
        self.requests.append(request)
        if request["QueueUrl"] == "https://queue.test/dlq":
            return {"Attributes": {"ApproximateNumberOfMessages": "4"}}
        return {
            "Attributes": {
                "ApproximateNumberOfMessages": "12",
                "ApproximateNumberOfMessagesNotVisible": "3",
            }
        }

    def start_message_move_task(self, **request):
        self.move_request = request
        return {"TaskHandle": "move-task-123"}


class DeliveryQueueSummaryTest(unittest.TestCase):
    def test_serializes_queue_counts(self):
        summary = DeliveryQueueSummary(pending=12, in_flight=3, failed=2)

        self.assertEqual(
            summary.to_dict(),
            {"pending": 12, "in_flight": 3, "failed": 2},
        )

    def test_rejects_negative_counts(self):
        with self.assertRaises(ValueError):
            DeliveryQueueSummary(pending=-1, in_flight=0, failed=0)


class SqsDeliveryAdminTest(unittest.TestCase):
    def test_reads_main_and_dead_letter_queue_counts(self):
        client = FakeSqsClient()
        operations = SqsDeliveryAdmin(
            client,
            "https://queue.test/delivery",
            "https://queue.test/dlq",
            "arn:queue",
            "arn:dlq",
        )

        summary = operations.summary()

        self.assertEqual(summary, DeliveryQueueSummary(12, 3, 4))
        self.assertEqual(len(client.requests), 2)
        self.assertIn(
            "ApproximateNumberOfMessagesNotVisible",
            client.requests[0]["AttributeNames"],
        )

    def test_starts_a_bounded_dead_letter_redrive(self):
        client = FakeSqsClient()
        operations = SqsDeliveryAdmin(
            client,
            "https://queue.test/delivery",
            "https://queue.test/dlq",
            "arn:queue",
            "arn:dlq",
        )

        task = operations.start_redrive(25)

        self.assertEqual(task, "move-task-123")
        self.assertEqual(
            client.move_request,
            {
                "SourceArn": "arn:dlq",
                "DestinationArn": "arn:queue",
                "MaxNumberOfMessagesPerSecond": 25,
            },
        )

    def test_rejects_an_unbounded_redrive_rate(self):
        operations = SqsDeliveryAdmin(
            FakeSqsClient(), "queue-url", "dlq-url", "queue-arn", "dlq-arn"
        )

        for rate in (0, 501):
            with self.subTest(rate=rate):
                with self.assertRaises(ValueError):
                    operations.start_redrive(rate)

    def test_normalizes_sqs_failures(self):
        class OfflineClient(FakeSqsClient):
            def get_queue_attributes(self, **request):
                raise RuntimeError("offline")

        operations = SqsDeliveryAdmin(
            OfflineClient(), "queue-url", "dlq-url", "queue-arn", "dlq-arn"
        )

        with self.assertRaises(DeliveryAdminError):
            operations.summary()


class DeliveryAdminConfigurationTest(unittest.TestCase):
    def test_returns_none_without_queue_configuration(self):
        self.assertIsNone(delivery_admin_from_env({}, FakeSqsClient()))

    def test_builds_the_sqs_adapter_from_environment(self):
        client = FakeSqsClient()
        operations = delivery_admin_from_env(
            {
                "DELIVERY_QUEUE_URL": "queue-url",
                "DELIVERY_DLQ_URL": "dlq-url",
                "DELIVERY_QUEUE_ARN": "queue-arn",
                "DELIVERY_DLQ_ARN": "dlq-arn",
            },
            client,
        )

        self.assertIsInstance(operations, SqsDeliveryAdmin)
        self.assertIs(operations.client, client)

    def test_rejects_partial_queue_configuration(self):
        with self.assertRaises(ValueError):
            delivery_admin_from_env(
                {"DELIVERY_QUEUE_URL": "queue-url"}, FakeSqsClient()
            )


if __name__ == "__main__":
    unittest.main()
