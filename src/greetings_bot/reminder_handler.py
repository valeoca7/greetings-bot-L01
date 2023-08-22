from typing import Dict, Mapping, Optional, Union

from greetings_bot.reminder_store import ReminderRepository
from greetings_bot.reminders import complete_reminder
from greetings_bot.telegram import Reply, reply_payload


class ScheduledReminderHandler:
    def __init__(self, reminders: ReminderRepository) -> None:
        self.reminders = reminders

    def handle(
        self, event: Mapping[str, object]
    ) -> Optional[Dict[str, Union[int, str]]]:
        try:
            owner_id = int(event["owner_id"])
            reminder_id = str(event["reminder_id"])
        except (KeyError, TypeError, ValueError):
            return None
        reminder = self.reminders.get(owner_id, reminder_id)
        if reminder is None or reminder.status != "pending":
            return None
        reply = Reply(reminder.chat_id, "Reminder: {}".format(reminder.text))
        self.reminders.save(complete_reminder(reminder))
        return reply_payload(reply)
