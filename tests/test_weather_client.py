import json
import unittest

from greetings_bot.weather_client import JsonHttpClient


class FakeResponse:
    def __init__(self, value, status=200):
        self.value = value
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return json.dumps(self.value).encode("utf-8")


class FakeOpener:
    def __init__(self, value, status=200):
        self.value = value
        self.status = status

    def __call__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        return FakeResponse(self.value, self.status)


class JsonHttpClientTest(unittest.TestCase):
    def test_gets_a_json_object_with_a_timeout(self):
        opener = FakeOpener({"daily": {}})

        value = JsonHttpClient(opener, timeout=4).get(
            "https://weather.test/forecast", {"latitude": 49.2, "days": 1}
        )

        self.assertEqual(value, {"daily": {}})
        self.assertIn("latitude=49.2", opener.url)
        self.assertIn("days=1", opener.url)
        self.assertEqual(opener.timeout, 4)

    def test_rejects_http_errors(self):
        client = JsonHttpClient(FakeOpener({}, status=503))

        with self.assertRaises(RuntimeError):
            client.get("https://weather.test", {})

    def test_rejects_invalid_json(self):
        class Response(FakeResponse):
            def read(self):
                return b"not json"

        class Opener:
            def __call__(self, url, timeout):
                return Response({})

        with self.assertRaises(ValueError):
            JsonHttpClient(Opener()).get("https://weather.test", {})

    def test_rejects_an_unbounded_timeout(self):
        with self.assertRaises(ValueError):
            JsonHttpClient(timeout=0)


if __name__ == "__main__":
    unittest.main()
