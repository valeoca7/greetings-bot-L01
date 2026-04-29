import json
import unittest
from pathlib import Path

from greetings_bot.delivery_queue import DeliveryMessage, message_to_body
from greetings_bot.replay import plan_replay


class ReplayPlanTest(unittest.TestCase):
    def test_plans_the_saved_delivery_batch_offline(self):
        event = json.loads(Path("events/delivery_batch.json").read_text())

        plan = plan_replay(event)

        self.assertEqual([message.id for message in plan.messages], ["local-delivery"])
        self.assertEqual(plan.rejected_record_ids, ())

    def test_separates_invalid_and_duplicate_records(self):
        body = message_to_body(DeliveryMessage("delivery-1", 42, "Hello", "greeting"))
        event = {
            "Records": [
                {"messageId": "one", "body": body},
                {"messageId": "duplicate", "body": body},
                {"messageId": "bad", "body": "{"},
            ]
        }

        plan = plan_replay(event)

        self.assertEqual(len(plan.messages), 1)
        self.assertEqual(plan.duplicate_record_ids, ("duplicate",))
        self.assertEqual(plan.rejected_record_ids, ("bad",))

    def test_rejects_unbounded_or_malformed_batches(self):
        for event, limit in (({"Records": "private"}, 10), ({"Records": [{}, {}]}, 1)):
            with self.subTest(event=event):
                with self.assertRaises(ValueError):
                    plan_replay(event, limit)


if __name__ == "__main__":
    unittest.main()
