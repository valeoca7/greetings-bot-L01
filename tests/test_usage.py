import unittest
from datetime import date

from greetings_bot.usage import (
    UsageBudgets,
    UsageMeter,
    usage_budgets_from_env,
    usage_meter_from_env,
)


class UsageBudgetsTest(unittest.TestCase):
    def test_uses_conservative_defaults(self):
        self.assertEqual(
            usage_budgets_from_env({}).public_snapshot(),
            (
                ("weather_calls", 500),
                ("information_requests", 100),
                ("queued_messages", 5000),
            ),
        )

    def test_reads_bounded_daily_budgets(self):
        budgets = usage_budgets_from_env(
            {
                "WEATHER_DAILY_BUDGET": "25",
                "INFORMATION_DAILY_BUDGET": "12",
                "QUEUE_DAILY_BUDGET": "300",
            }
        )

        self.assertEqual(budgets, UsageBudgets(25, 12, 300))

    def test_rejects_invalid_budgets(self):
        for environ, setting in (
            ({"WEATHER_DAILY_BUDGET": "0"}, "WEATHER_DAILY_BUDGET"),
            ({"INFORMATION_DAILY_BUDGET": "many"}, "INFORMATION_DAILY_BUDGET"),
            ({"QUEUE_DAILY_BUDGET": "1000001"}, "QUEUE_DAILY_BUDGET"),
        ):
            with self.subTest(environ=environ):
                with self.assertRaisesRegex(ValueError, setting):
                    usage_budgets_from_env(environ)

    def test_builds_a_meter_with_configured_budgets(self):
        meter = usage_meter_from_env({"QUEUE_DAILY_BUDGET": "700"})

        self.assertEqual(meter.budgets.queued_messages, 700)


class UsageMeterTest(unittest.TestCase):
    def test_counts_units_and_warns_once_at_the_soft_budget(self):
        meter = UsageMeter(UsageBudgets(weather_calls=2))

        with self.assertLogs("greetings_bot.usage", level="INFO") as logs:
            meter.record("weather_calls", 1, date(2026, 3, 1))
            meter.record("weather_calls", 1, date(2026, 3, 1))
            meter.record("weather_calls", 1, date(2026, 3, 1))

        self.assertEqual(meter.count("weather_calls"), 3)
        self.assertEqual(sum('"BudgetWarning":1' in line for line in logs.output), 1)

    def test_starts_a_new_counter_on_the_next_utc_day(self):
        meter = UsageMeter()
        meter.record("queued_messages", 4, date(2026, 3, 1))

        meter.record("queued_messages", 2, date(2026, 3, 2))

        self.assertEqual(meter.count("queued_messages"), 2)

    def test_rejects_private_dimensions_and_invalid_amounts(self):
        meter = UsageMeter()

        with self.assertRaises(ValueError):
            meter.record("user_42", 1, date(2026, 3, 1))
        with self.assertRaises(ValueError):
            meter.record("weather_calls", 0, date(2026, 3, 1))


if __name__ == "__main__":
    unittest.main()
