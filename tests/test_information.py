import unittest

from greetings_bot.information import InformationRequest, parse_information_request


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

    def test_rejects_missing_or_unknown_request_kind(self):
        for arguments in ((), ("person",), ("advice",)):
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    parse_information_request(arguments)

    def test_rejects_long_query(self):
        with self.assertRaisesRegex(ValueError, "too long"):
            parse_information_request(("place", "x" * 121))


if __name__ == "__main__":
    unittest.main()
