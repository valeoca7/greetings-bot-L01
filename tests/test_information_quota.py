import unittest
from datetime import datetime, timezone

from greetings_bot.information_quota import (
    InMemoryInformationQuota,
    weekly_window,
)


class InformationQuotaTest(unittest.TestCase):
    def test_uses_iso_week_and_next_utc_monday(self):
        window = weekly_window(
            datetime(2024, 10, 27, 23, 59, tzinfo=timezone.utc)
        )

        self.assertEqual(window.key, "2024-W43")
        self.assertEqual(
            window.resets_at,
            datetime(2024, 10, 28, tzinfo=timezone.utc),
        )

    def test_keeps_iso_year_at_calendar_boundary(self):
        window = weekly_window(
            datetime(2024, 12, 30, 8, 0, tzinfo=timezone.utc)
        )

        self.assertEqual(window.key, "2025-W01")
        self.assertEqual(
            window.resets_at,
            datetime(2025, 1, 6, tzinfo=timezone.utc),
        )

    def test_requires_a_timezone_aware_time(self):
        with self.assertRaises(ValueError):
            weekly_window(datetime(2024, 10, 21, 18, 0))

    def test_consumes_up_to_the_weekly_limit(self):
        quota = InMemoryInformationQuota()
        current_time = datetime(2024, 10, 22, tzinfo=timezone.utc)

        first = quota.consume(42, current_time, 2)
        second = quota.consume(42, current_time, 2)
        denied = quota.consume(42, current_time, 2)

        self.assertTrue(first.allowed)
        self.assertEqual(first.remaining, 1)
        self.assertTrue(second.allowed)
        self.assertEqual(second.remaining, 0)
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.remaining, 0)
        self.assertEqual(denied.resets_at.day, 28)

    def test_tracks_users_and_weeks_separately(self):
        quota = InMemoryInformationQuota()
        first_week = datetime(2024, 10, 27, tzinfo=timezone.utc)
        next_week = datetime(2024, 10, 28, tzinfo=timezone.utc)

        quota.consume(42, first_week, 1)

        self.assertTrue(quota.consume(7, first_week, 1).allowed)
        self.assertTrue(quota.consume(42, next_week, 1).allowed)

    def test_rejects_non_positive_limits(self):
        with self.assertRaises(ValueError):
            InMemoryInformationQuota().consume(
                42, datetime(2024, 10, 22, tzinfo=timezone.utc), 0
            )


if __name__ == "__main__":
    unittest.main()
