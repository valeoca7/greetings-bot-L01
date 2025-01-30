import hmac
from typing import Protocol

from greetings_bot.admin_api import AdminRequest


class AdminAuthorizer(Protocol):
    def authorize(self, request: AdminRequest) -> bool:
        ...


class BearerTokenAuthorizer:
    def __init__(self, token: str) -> None:
        if token != token.strip() or len(token) < 24:
            raise ValueError("admin token must contain at least 24 characters")
        self.token = token

    def authorize(self, request: AdminRequest) -> bool:
        value = request.headers.get("authorization", "")
        scheme, separator, candidate = value.partition(" ")
        if not separator or scheme.lower() != "bearer":
            return False
        return hmac.compare_digest(candidate, self.token)
