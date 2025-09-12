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
from greetings_bot.admin_config import dashboard_config_from_env
from greetings_bot.admin_delivery import SqsAdminClient, delivery_admin_from_env
from greetings_bot.clock import SystemClock
from greetings_bot.dynamo_notes import DynamoNoteRepository
from greetings_bot.dynamo_reminders import DynamoReminderRepository
from greetings_bot.dynamo_user_deletion import DynamoDeletionRequestRepository
from greetings_bot.dynamo_users import DynamoResource, repository_for_table
from greetings_bot.event_scheduler import SchedulerClient, scheduler_from_env
from greetings_bot.note_store import InMemoryNoteRepository
from greetings_bot.observability import correlation_id, log_event
from greetings_bot.reminder_store import InMemoryReminderRepository
from greetings_bot.user_data import UserDataExporter
from greetings_bot.user_data_cleanup import (
    DynamoUserDataCleaner,
    RepositoryUserDataCleaner,
)
from greetings_bot.user_deletion_service import UserDeletionService
from greetings_bot.user_deletion_store import (
    InMemoryDeletionRequestRepository,
)
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
    sqs_client: SqsAdminClient = None,
    scheduler_client: SchedulerClient = None,
) -> AdminLambdaHandler:
    token = environ.get("ADMIN_API_TOKEN", "")
    if not token.strip():
        raise ValueError("ADMIN_API_TOKEN is required")
    table_name = environ.get("USER_TABLE_NAME")
    if table_name:
        users = repository_for_table(table_name, dynamodb_resource)
        notes = DynamoNoteRepository(users.table)
        reminders = DynamoReminderRepository(users.table)
        deletion_requests = DynamoDeletionRequestRepository(users.table)
        cleaner = DynamoUserDataCleaner(users.table)
    else:
        users = InMemoryUserRepository()
        notes = InMemoryNoteRepository()
        reminders = InMemoryReminderRepository()
        deletion_requests = InMemoryDeletionRequestRepository()
        cleaner = RepositoryUserDataCleaner(users, notes, reminders)
    delivery = delivery_admin_from_env(environ, sqs_client)
    dashboard_config = dashboard_config_from_env(environ)
    exporter = UserDataExporter(users, notes, reminders)
    deletion = UserDeletionService(
        users,
        deletion_requests,
        SystemClock(),
        cleaner=cleaner,
        reminders=reminders,
        scheduler=scheduler_from_env(environ, scheduler_client),
    )
    application = AdminApplication(
        BearerTokenAuthorizer(token),
        users,
        delivery,
        dashboard_config,
        exporter,
        deletion=deletion,
    )
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
    if path == "/admin/dashboard":
        return "dashboard_view"
    if path == "/admin/dashboard/users":
        return "dashboard_users"
    if isinstance(path, str) and path.startswith(
        "/admin/dashboard/users/"
    ):
        return "dashboard_user_detail"
    if path == "/admin/dashboard/config":
        return "dashboard_config"
    if path == "/admin/dashboard/delivery":
        return "dashboard_delivery_status"
    if path == "/admin/dashboard/delivery/redrive":
        return "dashboard_delivery_redrive"
    if path == "/admin/users":
        return "users_list"
    if isinstance(path, str) and path.endswith("/deletion"):
        return "user_deletion_request"
    if isinstance(path, str) and path.endswith("/deletion/confirm"):
        return "user_deletion_confirm"
    if isinstance(path, str) and path.endswith("/deletion/execute"):
        return "user_deletion_execute"
    if (
        isinstance(path, str)
        and path.startswith("/admin/users/")
        and path.endswith("/export")
    ):
        return "user_export"
    if isinstance(path, str) and path.startswith("/admin/users/"):
        return "user_detail"
    if path == "/admin/delivery":
        return "delivery_status"
    if path == "/admin/delivery/redrive":
        return "delivery_redrive"
    return "unknown"
