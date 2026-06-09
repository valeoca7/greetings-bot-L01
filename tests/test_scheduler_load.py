import unittest
from datetime import datetime, timezone

from greetings_bot.clock import FixedClock
from greetings_bot.scheduler import GreetingDispatcher
from greetings_bot.users import InMemoryUserRepository
from tests.load_fixtures import synthetic_profiles


class SchedulerLoadFixtureTest(unittest.TestCase):
    def test_sparse_due_set_stops_after_the_dispatch_limit(self):
        now = datetime(2026, 6, 8, 18, 0, tzinfo=timezone.utc)
        visited = []

        def profiles():
            for user in synthetic_profiles(5000, now, due_every=50):
                visited.append(user.telegram_id)
                yield user

        dispatcher = GreetingDispatcher(
            InMemoryUserRepository(), FixedClock(now), max_batch=20
        )

        replies = dispatcher.dispatch(profiles())

        self.assertEqual(len(replies), 20)
        self.assertEqual(len(visited), 951)
        self.assertEqual(visited[-1], 951)

    def test_fixture_is_repeatable_across_timezones(self):
        now = datetime(2026, 6, 8, 18, 0, tzinfo=timezone.utc)

        first = list(synthetic_profiles(12, now, due_every=3))
        second = list(synthetic_profiles(12, now, due_every=3))

        self.assertEqual(first, second)
        self.assertGreater(len({user.timezone for user in first}), 3)


if __name__ == "__main__":
    unittest.main()
