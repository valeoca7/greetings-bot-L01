import json
from typing import Callable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class JsonHttpClient:
    def __init__(self, opener: Callable = urlopen, timeout: int = 5) -> None:
        if timeout < 1:
            raise ValueError("timeout must be positive")
        self.opener = opener
        self.timeout = timeout

    def get(self, endpoint: str, params: Mapping[str, object]) -> Mapping[str, object]:
        url = "{}?{}".format(endpoint, urlencode(params))
        request = Request(url, headers={"user-agent": "greetings-bot"})
        with self.opener(request, timeout=self.timeout) as response:
            if response.status >= 300:
                raise RuntimeError("weather request failed")
            value = json.loads(response.read().decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("weather response must be an object")
        return value
