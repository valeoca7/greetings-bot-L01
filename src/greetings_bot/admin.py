from greetings_bot import __version__
from typing import Optional, Union

from greetings_bot.admin_api import (
    AdminRequest,
    AdminRequestError,
    AdminResponse,
    HtmlResponse,
    JsonDownloadResponse,
)
from greetings_bot.admin_audit import audit_record_data, parse_audit_query
from greetings_bot.admin_auth import AdminAuthorizer
from greetings_bot.admin_config import DashboardConfig
from greetings_bot.admin_dashboard import (
    DashboardSnapshot,
    render_dashboard,
    render_config,
    render_audit,
    render_delivery,
    render_user_detail,
    render_user_list,
)
from greetings_bot.admin_delivery import DeliveryAdminError, DeliveryAdminOperations
from greetings_bot.admin_users import parse_user_query, search_users, user_detail
from greetings_bot.clock import Clock, SystemClock
from greetings_bot.configuration_audit import AuditRepository
from greetings_bot.user_data import UserDataExporter, UserDataExportError
from greetings_bot.user_deletion_service import (
    UserDeletionError,
    UserDeletionService,
)
from greetings_bot.users import UserRepository


class AdminApplication:
    def __init__(
        self,
        authorizer: AdminAuthorizer,
        users: UserRepository,
        delivery: Optional[DeliveryAdminOperations] = None,
        dashboard_config: Optional[DashboardConfig] = None,
        exporter: Optional[UserDataExporter] = None,
        clock: Optional[Clock] = None,
        deletion: Optional[UserDeletionService] = None,
        audit: Optional[AuditRepository] = None,
    ) -> None:
        self.authorizer = authorizer
        self.users = users
        self.delivery = delivery
        self.dashboard_config = dashboard_config
        self.exporter = exporter
        self.clock = clock or SystemClock()
        self.deletion = deletion
        self.audit = audit

    def handle(
        self, request: AdminRequest
    ) -> Union[AdminResponse, HtmlResponse, JsonDownloadResponse]:
        if not self.authorizer.authorize(request):
            return AdminResponse(401, {"error": "unauthorized"})
        if request.path.startswith("/admin/users/") and "/deletion" in request.path:
            return self._user_deletion(request)
        if request.path == "/admin/delivery/redrive":
            return self._redrive(request)
        if request.path == "/admin/dashboard/delivery/redrive":
            return self._dashboard_redrive(request)
        if request.method != "GET":
            return AdminResponse(405, {"error": "method not allowed"})
        if request.path == "/admin/health":
            return AdminResponse(200, {"status": "ok", "version": __version__})
        if request.path == "/admin/stats":
            return AdminResponse(200, {"users": self.users.count()})
        if request.path == "/admin/audit":
            if self.audit is None:
                return AdminResponse(503, {"error": "audit unavailable"})
            try:
                query = parse_audit_query(request.query)
                page = self.audit.query(query)
            except ValueError as error:
                return AdminResponse(400, {"error": str(error)})
            return AdminResponse(
                200,
                {
                    "items": [
                        audit_record_data(record) for record in page.records
                    ],
                    "next_cursor": page.next_cursor,
                },
            )
        if request.path == "/admin/dashboard":
            return self._dashboard()
        if request.path == "/admin/dashboard/config":
            if self.dashboard_config is None:
                return AdminResponse(503, {"error": "configuration unavailable"})
            return HtmlResponse(
                200, render_config(__version__, self.dashboard_config)
            )
        if request.path == "/admin/dashboard/audit":
            if self.audit is None:
                return AdminResponse(503, {"error": "audit unavailable"})
            try:
                query = parse_audit_query(request.query)
                page = self.audit.query(query)
            except ValueError as error:
                return AdminResponse(400, {"error": str(error)})
            return HtmlResponse(200, render_audit(__version__, page, query))
        if request.path == "/admin/dashboard/delivery":
            return self._dashboard_delivery()
        if request.path == "/admin/dashboard/users":
            try:
                query = parse_user_query(request.query)
            except ValueError as error:
                return AdminResponse(400, {"error": str(error)})
            page = search_users(self.users.all(), query)
            return HtmlResponse(200, render_user_list(__version__, page, query))
        if request.path.startswith("/admin/dashboard/users/"):
            raw_id = request.path[len("/admin/dashboard/users/") :]
            try:
                telegram_id = int(raw_id)
                if telegram_id < 1:
                    raise ValueError
            except ValueError:
                return AdminResponse(400, {"error": "invalid user id"})
            user = self.users.get(telegram_id)
            if user is None:
                return AdminResponse(404, {"error": "user not found"})
            return HtmlResponse(
                200, render_user_detail(__version__, user_detail(user))
            )
        if request.path == "/admin/delivery":
            if self.delivery is None:
                return AdminResponse(503, {"error": "delivery admin unavailable"})
            try:
                summary = self.delivery.summary()
            except DeliveryAdminError:
                return AdminResponse(503, {"error": "delivery admin unavailable"})
            return AdminResponse(200, summary.to_dict())
        if request.path == "/admin/users":
            try:
                query = parse_user_query(request.query)
            except ValueError as error:
                return AdminResponse(400, {"error": str(error)})
            page = search_users(self.users.all(), query)
            return AdminResponse(
                200,
                {
                    "items": list(page.items),
                    "next_cursor": page.next_cursor,
                },
            )
        if request.path.startswith("/admin/users/") and request.path.endswith(
            "/export"
        ):
            return self._export_user(request.path)
        if request.path.startswith("/admin/users/"):
            raw_id = request.path[len("/admin/users/") :]
            try:
                telegram_id = int(raw_id)
                if telegram_id < 1:
                    raise ValueError
            except ValueError:
                return AdminResponse(400, {"error": "invalid user id"})
            user = self.users.get(telegram_id)
            if user is None:
                return AdminResponse(404, {"error": "user not found"})
            return AdminResponse(200, user_detail(user))
        return AdminResponse(404, {"error": "not found"})

    def _user_deletion(self, request: AdminRequest) -> AdminResponse:
        if request.method != "POST":
            return AdminResponse(405, {"error": "method not allowed"})
        parts = request.path.strip("/").split("/")
        if len(parts) not in (4, 5) or parts[:2] != ["admin", "users"]:
            return AdminResponse(404, {"error": "not found"})
        if parts[3] != "deletion":
            return AdminResponse(404, {"error": "not found"})
        try:
            telegram_id = int(parts[2])
            if telegram_id < 1:
                raise ValueError
        except ValueError:
            return AdminResponse(400, {"error": "invalid user id"})
        if self.deletion is None:
            return AdminResponse(503, {"error": "user deletion unavailable"})
        action = "request" if len(parts) == 4 else parts[4]
        try:
            if action == "request":
                token = self.deletion.request(telegram_id)
                return AdminResponse(
                    201,
                    {
                        "status": "requested",
                        "confirmation_token": token,
                        "expires_in_seconds": 1800,
                    },
                )
            if action == "confirm":
                body = request.json_body()
                token = body.get("confirmation_token")
                if not isinstance(token, str):
                    raise ValueError("confirmation token is required")
                confirmed = self.deletion.confirm(telegram_id, token)
                return AdminResponse(200, {"status": confirmed.status})
            if action == "execute":
                completed = self.deletion.execute(telegram_id)
                return AdminResponse(200, {"status": completed.status})
            return AdminResponse(404, {"error": "not found"})
        except UserDeletionError as error:
            message = str(error)
            if message == "user not found":
                status = 404
            elif message in (
                "user deletion is unavailable",
                "user deletion needs another pass",
            ):
                status = 503
            else:
                status = 400
            return AdminResponse(status, {"error": message})
        except (AdminRequestError, ValueError) as error:
            return AdminResponse(400, {"error": str(error)})

    def _export_user(
        self, path: str
    ) -> Union[AdminResponse, JsonDownloadResponse]:
        raw_id = path[len("/admin/users/") : -len("/export")]
        try:
            telegram_id = int(raw_id)
            if telegram_id < 1:
                raise ValueError
        except ValueError:
            return AdminResponse(400, {"error": "invalid user id"})
        if self.exporter is None:
            return AdminResponse(503, {"error": "user export unavailable"})
        try:
            body = self.exporter.export(telegram_id, self.clock.now())
        except UserDataExportError as error:
            status = 404 if str(error) == "user not found" else 413
            return AdminResponse(status, {"error": str(error)})
        return JsonDownloadResponse(200, body)

    def _redrive(self, request: AdminRequest) -> AdminResponse:
        if request.method == "GET":
            if self.delivery is None:
                return AdminResponse(503, {"error": "delivery admin unavailable"})
            try:
                status = self.delivery.latest_redrive()
            except DeliveryAdminError:
                return AdminResponse(503, {"error": "delivery admin unavailable"})
            return AdminResponse(
                200, {"task": None if status is None else status.to_dict()}
            )
        if request.method == "DELETE":
            if self.delivery is None:
                return AdminResponse(503, {"error": "delivery admin unavailable"})
            try:
                body = request.json_body()
                task = body.get("task")
                if body.get("confirm") != "cancel_delivery_redrive":
                    raise ValueError("redrive cancellation confirmation is required")
                if not isinstance(task, str):
                    raise ValueError("redrive task handle is required")
                self.delivery.cancel_redrive(task)
            except DeliveryAdminError:
                return AdminResponse(503, {"error": "delivery admin unavailable"})
            except (AdminRequestError, ValueError) as error:
                return AdminResponse(400, {"error": str(error)})
            return AdminResponse(202, {"status": "cancelling"})
        if request.method != "POST":
            return AdminResponse(405, {"error": "method not allowed"})
        if self.delivery is None:
            return AdminResponse(503, {"error": "delivery admin unavailable"})
        try:
            body = request.json_body()
            rate = body.get("rate")
            if body.get("confirm") != "redrive_failed_deliveries":
                raise ValueError("redrive confirmation is required")
            if type(rate) is not int:
                raise ValueError("redrive rate is required")
            task = self.delivery.start_redrive(rate)
        except DeliveryAdminError:
            return AdminResponse(503, {"error": "delivery admin unavailable"})
        except (AdminRequestError, ValueError) as error:
            return AdminResponse(400, {"error": str(error)})
        return AdminResponse(202, {"task": task, "rate": rate})

    def _dashboard(self) -> HtmlResponse:
        users = self.users.all()
        active = sum(1 for user in users if user.enabled)
        values = {
            "users": len(users),
            "active_users": active,
            "disabled_users": len(users) - active,
        }
        if self.delivery is not None:
            try:
                delivery = self.delivery.summary()
                values.update(
                    pending=delivery.pending,
                    in_flight=delivery.in_flight,
                    failed=delivery.failed,
                )
            except DeliveryAdminError:
                pass
        snapshot = DashboardSnapshot(**values)
        return HtmlResponse(200, render_dashboard(__version__, snapshot))

    def _dashboard_delivery(
        self, feedback: Optional[str] = None, status_code: int = 200
    ) -> Union[AdminResponse, HtmlResponse]:
        if self.delivery is None:
            return AdminResponse(503, {"error": "delivery admin unavailable"})
        try:
            summary = self.delivery.summary()
        except DeliveryAdminError:
            return AdminResponse(503, {"error": "delivery admin unavailable"})
        return HtmlResponse(
            status_code, render_delivery(__version__, summary, feedback)
        )

    def _dashboard_redrive(
        self, request: AdminRequest
    ) -> Union[AdminResponse, HtmlResponse]:
        if request.method != "POST":
            return AdminResponse(405, {"error": "method not allowed"})
        if self.delivery is None:
            return AdminResponse(503, {"error": "delivery admin unavailable"})
        try:
            summary = self.delivery.summary()
            body = request.form_body()
            if body.get("confirm") != "redrive_failed_deliveries":
                raise ValueError("redrive confirmation is required")
            rate = int(body.get("rate", ""))
            self.delivery.start_redrive(rate)
        except DeliveryAdminError:
            return AdminResponse(503, {"error": "delivery admin unavailable"})
        except (AdminRequestError, ValueError) as error:
            return AdminResponse(400, {"error": str(error)})
        try:
            summary = self.delivery.summary()
        except DeliveryAdminError:
            pass
        return HtmlResponse(
            202,
            render_delivery(
                __version__, summary, "Redrive task started."
            ),
        )
