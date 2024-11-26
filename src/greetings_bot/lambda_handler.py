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
from greetings_bot.dynamo_information_quota import DynamoInformationQuota
from greetings_bot.event_scheduler import (
    NoopReminderScheduler,
    ReminderSchedulePort,
    scheduler_from_env,
)
from greetings_bot.information import InformationService
from greetings_bot.information_quota import (
    InformationQuota,
    InMemoryInformationQuota,
)
from greetings_bot.bedrock_information import BedrockClient
from greetings_bot.information_runtime import (
    information_requests_enabled,
    information_service_from_env,
    information_weekly_limit,
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
from greetings_bot.weather import WeatherProvider
from greetings_bot.weather_runtime import reliable_weather_provider


LambdaResponse = Dict[str, object]
LOGGER = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(
        self,
        users: UserRepository,
        notes: NoteRepository = None,
        reminders: ReminderRepository = None,
        reminder_scheduler: ReminderSchedulePort = None,
        weather_provider: WeatherProvider = None,
        information_service: InformationService = None,
        information_enabled: bool = False,
        information_quota: InformationQuota = None,
        information_weekly_limit: int = 5,
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
        self.weather_provider = weather_provider
        self.information_service = information_service
        self.information_enabled = information_enabled
        self.information_quota = information_quota
        self.information_weekly_limit = information_weekly_limit

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
                self.weather_provider,
                self.information_service,
                self.information_enabled,
                self.information_quota,
                self.information_weekly_limit,
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
    bedrock_client: BedrockClient = None,
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
    table = users.table if table_name else None
    weather_provider = reliable_weather_provider(environ, table)
    information_enabled = information_requests_enabled(environ)
    information_service = information_service_from_env(environ, bedrock_client)
    weekly_limit = information_weekly_limit(environ)
    information_quota = None
    if information_enabled:
        information_quota = (
            DynamoInformationQuota(table)
            if table is not None
            else InMemoryInformationQuota()
        )
    return WebhookHandler(
        users,
        notes,
        reminders,
        reminder_scheduler,
        weather_provider,
        information_service,
        information_enabled=information_enabled,
        information_quota=information_quota,
        information_weekly_limit=weekly_limit,
    )


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
