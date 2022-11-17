import json
import logging
from typing import Any, Dict, Mapping

from greetings_bot.api_gateway import (
    ApiGatewayRequest,
    ApiGatewayRequestError,
    ApiGatewayResponse,
)
from greetings_bot.runtime import process_payload
from greetings_bot.update_parser import UpdateParseError
from greetings_bot.users import InMemoryUserRepository, UserRepository


LambdaResponse = Dict[str, object]
LOGGER = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def handle(self, event: Mapping[str, Any]) -> LambdaResponse:
        try:
            request = ApiGatewayRequest.from_event(event)
            payload = request.json_body()
        except ApiGatewayRequestError as error:
            return self._error_response(str(error))
        try:
            reply = process_payload(payload, self.users)
        except UpdateParseError:
            return self._error_response("invalid update payload")
        body = "" if reply is None else json.dumps(reply)
        return ApiGatewayResponse(200, body).to_dict()

    @staticmethod
    def _error_response(message: str) -> LambdaResponse:
        return ApiGatewayResponse(400, json.dumps({"error": message})).to_dict()


_users = InMemoryUserRepository()
_handler = WebhookHandler(_users)


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> LambdaResponse:
    request_id = getattr(context, "aws_request_id", "local")
    LOGGER.info("handling webhook request %s", request_id)
    return _handler.handle(event)
