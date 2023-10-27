import json
import logging
import unittest
from types import SimpleNamespace

from greetings_bot.observability import correlation_id, emit_metric, log_event


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

    def test_uses_the_lambda_request_id_for_correlation(self):
        context = SimpleNamespace(aws_request_id="lambda-1")

        self.assertEqual(correlation_id({}, context), "lambda-1")

    def test_falls_back_to_the_gateway_request_id(self):
        event = {"requestContext": {"requestId": "gateway-1"}}

        self.assertEqual(correlation_id(event), "gateway-1")

    def test_uses_the_event_id_for_scheduled_invocations(self):
        self.assertEqual(correlation_id({"id": "schedule-1"}), "schedule-1")

    def test_writes_an_embedded_cloudwatch_metric(self):
        logger = logging.getLogger("tests.observability.metric")

        with self.assertLogs(logger, level="INFO") as logs:
            emit_metric(logger, "delivery", "Failed", 2, timestamp_ms=1234)

        payload = json.loads(logs.output[0].split(":", 2)[-1])
        self.assertEqual(payload["Service"], "delivery")
        self.assertEqual(payload["Failed"], 2)
        self.assertEqual(payload["_aws"]["Timestamp"], 1234)
        metric = payload["_aws"]["CloudWatchMetrics"][0]
        self.assertEqual(metric["Namespace"], "GreetingsBot")
        self.assertEqual(metric["Dimensions"], [["Service"]])


if __name__ == "__main__":
    unittest.main()
