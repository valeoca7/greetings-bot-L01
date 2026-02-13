import unittest

from greetings_bot.delivery_queue import (
    DeliveryMessage,
    SqsDeliveryQueue,
    message_from_body,
    message_to_body,
    queue_from_env,
)


class FakeQueueClient:
    def __init__(self):
        self.request = None
        self.attributes = {}
        self.batch_requests = []
        self.failed = []

    def send_message(self, **kwargs):
        self.request = kwargs
        return {"MessageId": "1"}

    def get_queue_attributes(self, **kwargs):
        self.request = kwargs
        return {"Attributes": self.attributes}

    def send_message_batch(self, **kwargs):
        self.batch_requests.append(kwargs)
        return {"Failed": self.failed}


class DeliveryMessageTest(unittest.TestCase):
    def test_round_trips_queue_body(self):
        message = DeliveryMessage(
            "reminder-42-abcd1234", 84, "Reminder: Call home", "reminder"
        )

        self.assertEqual(message_from_body(message_to_body(message)), message)

    def test_rejects_non_object_body(self):
        with self.assertRaisesRegex(ValueError, "object"):
            message_from_body("[]")

    def test_enqueues_serialized_message(self):
        client = FakeQueueClient()
        queue = SqsDeliveryQueue(client, "queue-url")
        message = DeliveryMessage("greeting-42", 84, "Good day", "greeting")

        queue.enqueue(message)

        self.assertEqual(client.request["QueueUrl"], "queue-url")
        self.assertEqual(message_from_body(client.request["MessageBody"]), message)

    def test_reports_total_approximate_depth(self):
        client = FakeQueueClient()
        client.attributes = {
            "ApproximateNumberOfMessages": "12",
            "ApproximateNumberOfMessagesNotVisible": "3",
            "ApproximateNumberOfMessagesDelayed": "2",
        }

        depth = SqsDeliveryQueue(client, "queue-url").depth()

        self.assertEqual(depth, 17)
        self.assertEqual(client.request["QueueUrl"], "queue-url")
        self.assertEqual(len(client.request["AttributeNames"]), 3)

    def test_treats_missing_depth_attributes_as_zero(self):
        self.assertEqual(SqsDeliveryQueue(FakeQueueClient(), "queue-url").depth(), 0)

    def test_enqueues_messages_in_sqs_sized_batches(self):
        client = FakeQueueClient()
        messages = [
            DeliveryMessage("greeting-{}".format(index), index, "Hello", "greeting")
            for index in range(23)
        ]

        SqsDeliveryQueue(client, "queue-url").enqueue_many(messages)

        self.assertEqual(
            [len(request["Entries"]) for request in client.batch_requests],
            [10, 10, 3],
        )
        self.assertEqual(
            message_from_body(client.batch_requests[2]["Entries"][2]["MessageBody"]),
            messages[-1],
        )

    def test_raises_when_sqs_rejects_part_of_a_batch(self):
        client = FakeQueueClient()
        client.failed = [{"Id": "0", "Code": "InternalError"}]

        with self.assertRaisesRegex(RuntimeError, "rejected"):
            SqsDeliveryQueue(client, "queue-url").enqueue_many(
                [DeliveryMessage("greeting-1", 1, "Hello", "greeting")]
            )

    def test_builds_queue_from_environment(self):
        queue = queue_from_env(
            {"DELIVERY_QUEUE_URL": "queue-url"}, FakeQueueClient()
        )

        self.assertIsInstance(queue, SqsDeliveryQueue)
        self.assertIsNone(queue_from_env({}, FakeQueueClient()))


if __name__ == "__main__":
    unittest.main()
