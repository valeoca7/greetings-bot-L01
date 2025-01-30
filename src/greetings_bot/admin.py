from greetings_bot import __version__
from greetings_bot.admin_api import AdminRequest, AdminResponse
from greetings_bot.admin_auth import AdminAuthorizer
from greetings_bot.users import UserRepository


class AdminApplication:
    def __init__(
        self, authorizer: AdminAuthorizer, users: UserRepository
    ) -> None:
        self.authorizer = authorizer
        self.users = users

    def handle(self, request: AdminRequest) -> AdminResponse:
        if not self.authorizer.authorize(request):
            return AdminResponse(401, {"error": "unauthorized"})
        if request.method != "GET":
            return AdminResponse(405, {"error": "method not allowed"})
        if request.path == "/admin/health":
            return AdminResponse(200, {"status": "ok", "version": __version__})
        if request.path == "/admin/stats":
            return AdminResponse(200, {"users": self.users.count()})
        return AdminResponse(404, {"error": "not found"})
