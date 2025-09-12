import secrets
from typing import Callable, Optional

from greetings_bot.clock import Clock
from greetings_bot.event_scheduler import ReminderSchedulePort
from greetings_bot.reminder_store import ReminderRepository
from greetings_bot.user_data_cleanup import UserDataCleaner
from greetings_bot.user_deletion import (
    DeletionRequest,
    complete_deletion,
    confirm_deletion,
)
from greetings_bot.user_deletion import request_deletion as new_request
from greetings_bot.user_deletion_store import DeletionRequestRepository
from greetings_bot.users import UserRepository


class UserDeletionError(RuntimeError):
    pass


class UserDeletionService:
    def __init__(
        self,
        users: UserRepository,
        requests: DeletionRequestRepository,
        clock: Clock,
        token_factory: Callable[[], str] = None,
        cleaner: Optional[UserDataCleaner] = None,
        reminders: Optional[ReminderRepository] = None,
        scheduler: Optional[ReminderSchedulePort] = None,
    ) -> None:
        self.users = users
        self.requests = requests
        self.clock = clock
        self.token_factory = token_factory or (
            lambda: secrets.token_urlsafe(24)
        )
        self.cleaner = cleaner
        self.reminders = reminders
        self.scheduler = scheduler

    def request(self, telegram_id: int) -> str:
        if self.users.get(telegram_id) is None:
            raise UserDeletionError("user not found")
        token = self.token_factory()
        request = new_request(telegram_id, token, self.clock.now())
        self.requests.save(request)
        return token

    def confirm(self, telegram_id: int, token: str) -> DeletionRequest:
        request = self.requests.get(telegram_id)
        if request is None:
            raise UserDeletionError("deletion request not found")
        try:
            confirmed = confirm_deletion(request, token, self.clock.now())
        except ValueError as error:
            raise UserDeletionError(str(error)) from error
        self.requests.save(confirmed)
        return confirmed

    def execute(
        self, telegram_id: int, max_batches: int = 20
    ) -> DeletionRequest:
        request = self.requests.get(telegram_id)
        if request is None or request.status != "confirmed":
            raise UserDeletionError("deletion request is not confirmed")
        if self.cleaner is None or self.reminders is None or self.scheduler is None:
            raise UserDeletionError("user deletion is unavailable")
        if not 1 <= max_batches <= 100:
            raise ValueError("deletion batch count must be between 1 and 100")
        for reminder in self.reminders.all_for(telegram_id):
            if reminder.recurrence is None and reminder.status in (
                "pending",
                "paused",
            ):
                self.scheduler.delete(reminder)
        for _ in range(max_batches):
            batch = self.cleaner.erase_batch(telegram_id)
            if batch.complete:
                completed = complete_deletion(request, self.clock.now())
                self.requests.save(completed)
                return completed
        raise UserDeletionError("user deletion needs another pass")
