import json
from typing import Any, Dict, Mapping, Union

from greetings_bot.api_gateway import ApiGatewayRequest, ApiGatewayResponse
from greetings_bot.runtime import process_payload
from greetings_bot.users import InMemoryUserRepository, UserRepository


LambdaResponse = Dict[str, Union[int, str]]


class WebhookHandler:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def handle(self, event: Mapping[str, Any]) -> LambdaResponse:
        request = ApiGatewayRequest.from_event(event)
        reply = process_payload(request.json_body(), self.users)
        body = "" if reply is None else json.dumps(reply)
        return ApiGatewayResponse(200, body).to_dict()


_users = InMemoryUserRepository()
_handler = WebhookHandler(_users)


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> LambdaResponse:
    return _handler.handle(event)
