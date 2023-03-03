import json
import logging
import os
from typing import Any, Dict, Mapping

from greetings_bot.api_gateway import (
    ApiGatewayRequest,
    ApiGatewayRequestError,
    ApiGatewayResponse,
)
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.dynamo_notes import DynamoNoteRepository
from greetings_bot.note_store import InMemoryNoteRepository, NoteRepository
from greetings_bot.runtime import process_payload
from greetings_bot.update_parser import UpdateParseError
from greetings_bot.users import InMemoryUserRepository, UserRepository


LambdaResponse = Dict[str, object]
LOGGER = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(
        self,
        users: UserRepository,
        notes: NoteRepository = None,
    ) -> None:
        self.users = users
        self.notes = notes if notes is not None else InMemoryNoteRepository()

    def handle(self, event: Mapping[str, Any]) -> LambdaResponse:
        try:
            request = ApiGatewayRequest.from_event(event)
            payload = request.json_body()
        except ApiGatewayRequestError as error:
            return self._error_response(str(error))
        try:
            reply = process_payload(payload, self.users, self.notes)
        except UpdateParseError:
            return self._error_response("invalid update payload")
        body = "" if reply is None else json.dumps(reply)
        return ApiGatewayResponse(200, body).to_dict()

    @staticmethod
    def _error_response(message: str) -> LambdaResponse:
        return ApiGatewayResponse(400, json.dumps({"error": message})).to_dict()


def build_default_handler(
    environ: Mapping[str, str] = os.environ,
    dynamodb_resource: DynamoResource = None,
) -> WebhookHandler:
    table_name = environ.get("USER_TABLE_NAME")
    if table_name:
        users = repository_for_table(table_name, dynamodb_resource)
        notes = DynamoNoteRepository(users.table)
    else:
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
    return WebhookHandler(users, notes)


_handler = build_default_handler()


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> LambdaResponse:
    request_id = getattr(context, "aws_request_id", "local")
    LOGGER.info("handling webhook request %s", request_id)
    return _handler.handle(event)
