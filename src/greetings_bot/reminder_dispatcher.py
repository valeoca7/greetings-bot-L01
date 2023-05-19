import logging
from typing import List

from greetings_bot.clock import Clock
from greetings_bot.reminder_store import ReminderRepository
from greetings_bot.reminders import complete_reminder
from greetings_bot.telegram import Reply


LOGGER = logging.getLogger(__name__)


class ReminderDispatcher:
    def __init__(
        self,
        reminders: ReminderRepository,
        clock: Clock,
        max_batch: int = 100,
    ) -> None:
        self.reminders = reminders
        self.clock = clock
        self.max_batch = max_batch

    def dispatch(self) -> List[Reply]:
        due = self.reminders.due_before(self.clock.now(), self.max_batch)
        LOGGER.info("dispatching %d reminders", len(due))
        replies = [
            Reply(reminder.chat_id, "Reminder: {}".format(reminder.text))
            for reminder in due
        ]
        for reminder in due:
            self.reminders.save(complete_reminder(reminder))
        return replies
