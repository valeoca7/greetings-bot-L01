import logging
import os
from typing import Any, Dict, Mapping, Optional

from greetings_bot.admin import AdminApplication
from greetings_bot.admin_api import (
    AdminRequest,
    AdminRequestError,
    AdminResponse,
)
from greetings_bot.admin_auth import BearerTokenAuthorizer
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.observability import correlation_id, log_event
from greetings_bot.users import InMemoryUserRepository


LOGGER = logging.getLogger(__name__)


class AdminLambdaHandler:
    def __init__(self, application: AdminApplication) -> None:
        self.application = application

    def handle(self, event: Mapping[str, Any]) -> Dict[str, object]:
        try:
            request = AdminRequest.from_event(event)
        except AdminRequestError as error:
            return AdminResponse(400, {"error": str(error)}).to_dict()
        return self.application.handle(request).to_dict()


def build_default_handler(
    environ: Mapping[str, str] = os.environ,
    dynamodb_resource: DynamoResource = None,
) -> AdminLambdaHandler:
    token = environ.get("ADMIN_API_TOKEN", "")
    if not token.strip():
        raise ValueError("ADMIN_API_TOKEN is required")
    table_name = environ.get("USER_TABLE_NAME")
    users = (
        repository_for_table(table_name, dynamodb_resource)
        if table_name
        else InMemoryUserRepository()
    )
    application = AdminApplication(BearerTokenAuthorizer(token), users)
    return AdminLambdaHandler(application)


_handler: Optional[AdminLambdaHandler] = None


def handle_event(
    event: Mapping[str, Any], context: object = None
) -> Dict[str, object]:
    global _handler
    if _handler is None:
        _handler = build_default_handler()
    response = _handler.handle(event)
    status_code = int(response["statusCode"])
    log_event(
        LOGGER,
        "admin_request_complete",
        logging.WARNING if status_code >= 400 else logging.INFO,
        action=_audit_action(event),
        request_id=correlation_id(event, context),
        status_code=status_code,
    )
    return response


def _audit_action(event: Mapping[str, Any]) -> str:
    path = event.get("rawPath") or event.get("path")
    if path == "/admin/health":
        return "health_read"
    if path == "/admin/stats":
        return "stats_read"
    if path == "/admin/users":
        return "users_list"
    if isinstance(path, str) and path.startswith("/admin/users/"):
        return "user_detail"
    return "unknown"
