import json
import unittest
from pathlib import Path

from greetings_bot.delivery_queue import DeliveryMessage, message_to_body
from greetings_bot.queue_worker import (
    DeliveryQueueWorker,
    InMemoryDeliveryReceiptLedger,
    build_default_worker,
)
from greetings_bot.dynamo_receipts import DynamoDeliveryReceiptLedger


class FakeSender:
    def __init__(self, fail=False, error=RuntimeError):
        self.messages = []
        self.fail = fail
        self.error = error

    def send(self, message):
        if self.fail:
            raise self.error("send failed")
        self.messages.append(message)


def sqs_event(message, message_id="sqs-1"):
    return {
        "Records": [
            {"messageId": message_id, "body": message_to_body(message)}
        ]
    }


class DeliveryQueueWorkerTest(unittest.TestCase):
    def test_saved_queue_event_can_be_processed(self):
        path = Path(__file__).parents[1] / "events" / "delivery_batch.json"
        event = json.loads(path.read_text())
        sender = FakeSender()

        result = DeliveryQueueWorker(
            sender, InMemoryDeliveryReceiptLedger()
        ).handle(event)

        self.assertEqual(result, {"batchItemFailures": []})
        self.assertEqual(sender.messages[0].id, "local-delivery")

    def test_sends_queue_message_and_records_receipt(self):
        sender = FakeSender()
        receipts = InMemoryDeliveryReceiptLedger()
        worker = DeliveryQueueWorker(sender, receipts)
        message = DeliveryMessage("delivery-1", 42, "Hello", "greeting")

        with self.assertLogs("greetings_bot.queue_worker", level="INFO") as logs:
            result = worker.handle(sqs_event(message))

        self.assertEqual(sender.messages, [message])
        self.assertTrue(receipts.contains("delivery-1"))
        self.assertEqual(result, {"batchItemFailures": []})
        self.assertTrue(any('"Delivered":1' in line for line in logs.output))

    def test_skips_duplicate_delivery(self):
        sender = FakeSender()
        receipts = InMemoryDeliveryReceiptLedger()
        receipts.record("delivery-1")
        worker = DeliveryQueueWorker(sender, receipts)

        worker.handle(
            sqs_event(DeliveryMessage("delivery-1", 42, "Hello", "greeting"))
        )

        self.assertEqual(sender.messages, [])

    def test_returns_failed_record_for_retry(self):
        worker = DeliveryQueueWorker(
            FakeSender(fail=True), InMemoryDeliveryReceiptLedger()
        )

        result = worker.handle(
            sqs_event(DeliveryMessage("delivery-1", 42, "Hello", "greeting"))
        )

        self.assertEqual(
            result, {"batchItemFailures": [{"itemIdentifier": "sqs-1"}]}
        )

    def test_retries_a_malformed_message(self):
        worker = DeliveryQueueWorker(
            FakeSender(), InMemoryDeliveryReceiptLedger()
        )

        with self.assertLogs("greetings_bot.queue_worker", level="WARNING"):
            result = worker.handle(
                {"Records": [{"messageId": "bad-1", "body": "{"}]}
            )

        self.assertEqual(
            result, {"batchItemFailures": [{"itemIdentifier": "bad-1"}]}
        )

    def test_retries_transport_errors(self):
        worker = DeliveryQueueWorker(
            FakeSender(fail=True, error=OSError),
            InMemoryDeliveryReceiptLedger(),
        )

        result = worker.handle(
            sqs_event(DeliveryMessage("delivery-2", 42, "Hello", "greeting"))
        )

        self.assertEqual(
            result, {"batchItemFailures": [{"itemIdentifier": "sqs-1"}]}
        )

    def test_logs_failed_delivery(self):
        worker = DeliveryQueueWorker(
            FakeSender(fail=True), InMemoryDeliveryReceiptLedger()
        )

        with self.assertLogs("greetings_bot.queue_worker", level="WARNING") as logs:
            worker.handle(
                sqs_event(DeliveryMessage("delivery-1", 42, "Hello", "greeting")),
                "request-7",
            )

        self.assertIn('"delivery_id":"delivery-1"', logs.output[0])
        self.assertIn('"message_id":"sqs-1"', logs.output[0])
        self.assertIn('"request_id":"request-7"', logs.output[0])

    def test_builds_worker_with_dynamo_receipts(self):
        class Resource:
            def Table(self, name):
                self.name = name
                return object()

        resource = Resource()

        worker = build_default_worker(
            {"USER_TABLE_NAME": "data"}, resource, FakeSender()
        )

        self.assertEqual(resource.name, "data")
        self.assertIsInstance(worker.receipts, DynamoDeliveryReceiptLedger)


if __name__ == "__main__":
    unittest.main()
