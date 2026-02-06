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

    def send_message(self, **kwargs):
        self.request = kwargs
        return {"MessageId": "1"}

    def get_queue_attributes(self, **kwargs):
        self.request = kwargs
        return {"Attributes": self.attributes}


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

    def test_builds_queue_from_environment(self):
        queue = queue_from_env(
            {"DELIVERY_QUEUE_URL": "queue-url"}, FakeQueueClient()
        )

        self.assertIsInstance(queue, SqsDeliveryQueue)
        self.assertIsNone(queue_from_env({}, FakeQueueClient()))


if __name__ == "__main__":
    unittest.main()
