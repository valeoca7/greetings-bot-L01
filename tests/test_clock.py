import unittest
from datetime import datetime

from greetings_bot.clock import FixedClock, SystemClock


class SystemClockTest(unittest.TestCase):
    def test_returns_current_datetime(self):
        before = datetime.now()
        current = SystemClock().now()
        after = datetime.now()

        self.assertLessEqual(before, current)
        self.assertLessEqual(current, after)

    def test_fixed_clock_keeps_supplied_time(self):
        current = datetime(2022, 8, 9, 20, 15)

        self.assertEqual(current, FixedClock(current).now())


if __name__ == "__main__":
    unittest.main()
