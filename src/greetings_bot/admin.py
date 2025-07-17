from greetings_bot import __version__
from typing import Optional, Union

from greetings_bot.admin_api import (
    AdminRequest,
    AdminRequestError,
    AdminResponse,
    HtmlResponse,
)
from greetings_bot.admin_auth import AdminAuthorizer
from greetings_bot.admin_config import DashboardConfig
from greetings_bot.admin_dashboard import (
    DashboardSnapshot,
    render_dashboard,
    render_config,
    render_delivery,
    render_user_detail,
    render_user_list,
)
from greetings_bot.admin_delivery import DeliveryAdminError, DeliveryAdminOperations
from greetings_bot.admin_users import parse_user_query, search_users, user_detail
from greetings_bot.users import UserRepository


class AdminApplication:
    def __init__(
        self,
        authorizer: AdminAuthorizer,
        users: UserRepository,
        delivery: Optional[DeliveryAdminOperations] = None,
        dashboard_config: Optional[DashboardConfig] = None,
    ) -> None:
        self.authorizer = authorizer
        self.users = users
        self.delivery = delivery
        self.dashboard_config = dashboard_config

    def handle(
        self, request: AdminRequest
    ) -> Union[AdminResponse, HtmlResponse]:
        if not self.authorizer.authorize(request):
            return AdminResponse(401, {"error": "unauthorized"})
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
        if request.path == "/admin/dashboard":
            return self._dashboard()
        if request.path == "/admin/dashboard/config":
            if self.dashboard_config is None:
                return AdminResponse(503, {"error": "configuration unavailable"})
            return HtmlResponse(
                200, render_config(__version__, self.dashboard_config)
            )
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

    def _redrive(self, request: AdminRequest) -> AdminResponse:
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
            body = request.form_body()
            if body.get("confirm") != "redrive_failed_deliveries":
                raise ValueError("redrive confirmation is required")
            rate = int(body.get("rate", ""))
            self.delivery.start_redrive(rate)
        except DeliveryAdminError:
            return AdminResponse(503, {"error": "delivery admin unavailable"})
        except (AdminRequestError, ValueError) as error:
            return AdminResponse(400, {"error": str(error)})
        return self._dashboard_delivery("Redrive task started.", 202)
