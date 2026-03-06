import unittest
from datetime import datetime, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.information import (
    InformationRequest,
    InformationService,
    parse_information_request,
)
from greetings_bot.usage import UsageBudgets, UsageMeter


class FakeProvider:
    def __init__(self, response):
        self.response = response

    def answer(self, request):
        self.request = request
        return self.response


class InformationRequestTest(unittest.TestCase):
    def test_parses_joke_and_fact_requests(self):
        self.assertEqual(
            parse_information_request(("joke",)),
            InformationRequest("joke"),
        )
        self.assertEqual(
            parse_information_request(("fact",)),
            InformationRequest("fact"),
        )

    def test_parses_person_and_place_queries(self):
        self.assertEqual(
            parse_information_request(("person", "Ada", "Lovelace")),
            InformationRequest("person", "Ada Lovelace"),
        )
        self.assertEqual(
            parse_information_request(("place", "Victoria", "BC")),
            InformationRequest("place", "Victoria BC"),
        )

    def test_parses_a_short_advice_topic(self):
        self.assertEqual(
            parse_information_request(("advice", "build", "a", "sleep", "routine")),
            InformationRequest("advice", "build a sleep routine"),
        )

    def test_rejects_missing_or_unknown_request_kind(self):
        for arguments in ((), ("person",), ("advice",), ("recipe", "soup")):
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    parse_information_request(arguments)

    def test_rejects_long_query(self):
        with self.assertRaisesRegex(ValueError, "too long"):
            parse_information_request(("place", "x" * 121))

    def test_service_delegates_to_provider(self):
        provider = FakeProvider("  A short fact.  ")
        service = InformationService(provider)
        request = InformationRequest("fact")

        answer = service.answer(request)

        self.assertEqual(answer, "A short fact.")
        self.assertEqual(provider.request, request)

    def test_service_rejects_empty_or_long_answers(self):
        for response in ("  ", "x" * 601):
            with self.subTest(length=len(response)):
                with self.assertRaises(ValueError):
                    InformationService(FakeProvider(response)).answer(
                        InformationRequest("fact")
                    )

    def test_counts_provider_attempts_without_request_content(self):
        meter = UsageMeter(UsageBudgets(information_requests=2))
        service = InformationService(
            FakeProvider("A fact."),
            usage_meter=meter,
            clock=FixedClock(datetime(2026, 3, 5, tzinfo=timezone.utc)),
        )

        service.answer(InformationRequest("person", "Private Name"))

        self.assertEqual(meter.count("information_requests"), 1)
        self.assertNotIn("Private Name", repr(meter.__dict__))


if __name__ == "__main__":
    unittest.main()
