from greetings_bot import __version__
from typing import Optional

from greetings_bot.admin_api import AdminRequest, AdminRequestError, AdminResponse
from greetings_bot.admin_auth import AdminAuthorizer
from greetings_bot.admin_delivery import DeliveryAdminError, DeliveryAdminOperations
from greetings_bot.admin_users import parse_user_query, search_users, user_detail
from greetings_bot.users import UserRepository


class AdminApplication:
    def __init__(
        self,
        authorizer: AdminAuthorizer,
        users: UserRepository,
        delivery: Optional[DeliveryAdminOperations] = None,
    ) -> None:
        self.authorizer = authorizer
        self.users = users
        self.delivery = delivery

    def handle(self, request: AdminRequest) -> AdminResponse:
        if not self.authorizer.authorize(request):
            return AdminResponse(401, {"error": "unauthorized"})
        if request.path == "/admin/delivery/redrive":
            return self._redrive(request)
        if request.method != "GET":
            return AdminResponse(405, {"error": "method not allowed"})
        if request.path == "/admin/health":
            return AdminResponse(200, {"status": "ok", "version": __version__})
        if request.path == "/admin/stats":
            return AdminResponse(200, {"users": self.users.count()})
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
