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
from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.event_scheduler import (
    NoopReminderScheduler,
    ReminderSchedulePort,
    scheduler_from_env,
)
from greetings_bot.note_store import InMemoryNoteRepository, NoteRepository
from greetings_bot.observability import correlation_id, emit_metric, log_event
from greetings_bot.reminder_store import (
    InMemoryReminderRepository,
    ReminderRepository,
)
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
        reminders: ReminderRepository = None,
        reminder_scheduler: ReminderSchedulePort = None,
    ) -> None:
        self.users = users
        self.notes = notes if notes is not None else InMemoryNoteRepository()
        self.reminders = (
            reminders if reminders is not None else InMemoryReminderRepository()
        )
        self.reminder_scheduler = (
            reminder_scheduler
            if reminder_scheduler is not None
            else NoopReminderScheduler()
        )

    def handle(self, event: Mapping[str, Any]) -> LambdaResponse:
        try:
            request = ApiGatewayRequest.from_event(event)
            payload = request.json_body()
        except ApiGatewayRequestError as error:
            return self._error_response(str(error))
        try:
            reply = process_payload(
                payload,
                self.users,
                self.notes,
                self.reminders,
                self.reminder_scheduler,
            )
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
        reminders = DynamoReminderRepository(users.table)
    else:
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        reminders = InMemoryReminderRepository()
    reminder_scheduler = scheduler_from_env(environ)
    return WebhookHandler(users, notes, reminders, reminder_scheduler)


_handler = build_default_handler()


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> LambdaResponse:
    request_id = correlation_id(event, context)
    log_event(LOGGER, "webhook_received", request_id=request_id)
    response = _handler.handle(event)
    status_code = int(response["statusCode"])
    log_event(
        LOGGER,
        "webhook_complete",
        logging.WARNING if status_code >= 400 else logging.INFO,
        request_id=request_id,
        status_code=status_code,
    )
    emit_metric(LOGGER, "webhook", "Requests")
    emit_metric(
        LOGGER,
        "webhook",
        "ClientError",
        int(status_code >= 400),
    )
    return response
