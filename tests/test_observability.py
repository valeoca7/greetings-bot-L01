import json
import logging
import unittest

from greetings_bot.observability import log_event


class ObservabilityTest(unittest.TestCase):
    def test_writes_a_structured_event(self):
        logger = logging.getLogger("tests.observability")

        with self.assertLogs(logger, level="INFO") as logs:
            log_event(logger, "dispatch_complete", count=3, request_id="req-1")

        payload = json.loads(logs.output[0].split(":", 2)[-1])
        self.assertEqual(
            payload,
            {"event": "dispatch_complete", "count": 3, "request_id": "req-1"},
        )

    def test_accepts_a_warning_level(self):
        logger = logging.getLogger("tests.observability.warning")

        with self.assertLogs(logger, level="WARNING") as logs:
            log_event(logger, "delivery_failed", logging.WARNING, attempt=2)

        self.assertIn('"attempt":2', logs.output[0])


if __name__ == "__main__":
    unittest.main()
