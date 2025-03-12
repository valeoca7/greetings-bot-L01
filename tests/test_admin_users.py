import unittest

from greetings_bot.admin_users import (
    AdminUserQuery,
    decode_user_cursor,
    search_users,
    parse_user_query,
    user_detail,
)
from greetings_bot.users import User


class AdminUserQueryTest(unittest.TestCase):
    def test_uses_bounded_defaults(self):
        self.assertEqual(
            parse_user_query({}),
            AdminUserQuery(term="", status="all", limit=20),
        )

    def test_reads_search_status_and_limit(self):
        self.assertEqual(
            parse_user_query(
                {"q": "  Mira  ", "status": "disabled", "limit": "7"}
            ),
            AdminUserQuery(term="Mira", status="disabled", limit=7),
        )

    def test_rejects_invalid_filters(self):
        for params in (
            {"status": "pending"},
            {"limit": "0"},
            {"limit": "51"},
            {"limit": "many"},
            {"q": "x" * 51},
        ):
            with self.subTest(params=params):
                with self.assertRaises(ValueError):
                    parse_user_query(params)

    def test_reads_an_opaque_cursor(self):
        first = search_users(
            (User(7, 7, "Sam"), User(42, 42, "Mira")),
            AdminUserQuery(limit=1),
        )

        query = parse_user_query({"cursor": first.next_cursor})

        self.assertEqual(query.after_id, 7)

    def test_rejects_a_malformed_cursor(self):
        with self.assertRaises(ValueError):
            decode_user_cursor("not-a-cursor")


class AdminUserSearchTest(unittest.TestCase):
    def setUp(self):
        self.users = (
            User(42, 4200, "Mira", timezone="America/Vancouver"),
            User(7, 7000, "Sam", enabled=False),
            User(99, 9900, "Amira"),
        )

    def test_returns_safe_summaries_in_id_order(self):
        page = search_users(self.users, AdminUserQuery())

        self.assertEqual([item["id"] for item in page.items], [7, 42, 99])
        self.assertEqual(page.items[0]["status"], "disabled")
        self.assertNotIn("chat_id", page.items[0])

    def test_filters_by_name_id_and_status(self):
        by_name = search_users(
            self.users, AdminUserQuery(term="mira", status="active")
        )
        by_id = search_users(self.users, AdminUserQuery(term="7"))

        self.assertEqual([item["id"] for item in by_name.items], [42, 99])
        self.assertEqual([item["id"] for item in by_id.items], [7])

    def test_reports_more_results_after_the_limit(self):
        page = search_users(self.users, AdminUserQuery(limit=2))

        self.assertEqual(len(page.items), 2)
        self.assertTrue(page.has_more)
        self.assertIsNotNone(page.next_cursor)

    def test_continues_after_the_cursor_id(self):
        page = search_users(
            self.users, AdminUserQuery(limit=2, after_id=42)
        )

        self.assertEqual([item["id"] for item in page.items], [99])
        self.assertFalse(page.has_more)
        self.assertIsNone(page.next_cursor)


class AdminUserDetailTest(unittest.TestCase):
    def test_returns_profile_preferences_without_chat_identity(self):
        detail = user_detail(
            User(
                42,
                4200,
                "Mira",
                locale="en",
                greeting_time="18:30",
                timezone="America/Vancouver",
                quiet_start="22:00",
                quiet_end="07:00",
                greeting_days=("mon", "wed", "fri"),
                digest_mode="daily",
                weather_units="imperial",
                weather_summary=True,
            )
        )

        self.assertEqual(detail["id"], 42)
        self.assertEqual(detail["preferences"]["greeting_time"], "18:30")
        self.assertEqual(
            detail["preferences"]["greeting_days"], ["mon", "wed", "fri"]
        )
        self.assertEqual(
            detail["preferences"]["quiet_hours"],
            {"start": "22:00", "end": "07:00"},
        )
        self.assertNotIn("chat_id", detail)


if __name__ == "__main__":
    unittest.main()
