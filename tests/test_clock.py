import unittest
from datetime import datetime

from greetings_bot.clock import SystemClock


class SystemClockTest(unittest.TestCase):
    def test_returns_current_datetime(self):
        before = datetime.now()
        current = SystemClock().now()
        after = datetime.now()

        self.assertLessEqual(before, current)
        self.assertLessEqual(current, after)


if __name__ == "__main__":
    unittest.main()
