import os
import tempfile
import time
import unittest
from unittest import mock

from tests.helpers import issue, log_in, make_app
from webapp.players import Players


class PortfolioOffTests(unittest.TestCase):
    def test_no_portfolio_login_without_config(self):
        client = make_app(self).test_client()
        self.assertNotIn(b"Log in with portfolio account", client.get("/").data)
        self.assertEqual(client.get("/sso/login").status_code, 404)


class PortfolioLoginTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app(self, portfolio=True)

    def log_in(self, client, sub="1", token=None):
        return log_in(client, sub, token)

    def range_weapon(self, client):
        with client.session_transaction() as session:
            return session.get("range", {}).get("weapon")

    def test_login_shows_account_and_logout_keeps_browser_save(self):
        client = self.app.test_client()
        page = client.get("/").data
        self.assertIn(b"Log in with portfolio account", page)
        self.assertIn(b'data-portfolio-url="http://portfolio.test"', page)
        self.assertEqual(self.log_in(client).status_code, 302)
        self.assertIn(b"ronovo: Log out", client.get("/").data)
        client.post("/range/setup", data={"weapon": "M1911", "size": "s", "distance": "50"})
        client.post("/logout")
        self.assertIn(b"Log in with portfolio account", client.get("/").data)
        self.assertEqual(self.range_weapon(client), "M1911")

    def test_progress_follows_the_account_to_another_browser(self):
        first = self.app.test_client()
        self.log_in(first)
        first.post("/range/setup", data={"weapon": "M1911", "size": "s", "distance": "50"})
        with mock.patch("random.Random.randint", return_value=1):
            for _ in range(3):
                first.post("/range/fire")
        with first.session_transaction() as session:
            destroyed = session.get("destroyed", 0)
        self.assertGreater(destroyed, 0)

        second = self.app.test_client()
        self.log_in(second)
        self.assertEqual(self.range_weapon(second), "M1911")
        with second.session_transaction() as session:
            self.assertEqual(session.get("destroyed", 0), destroyed)

    def test_newer_browser_progress_wins_over_the_account(self):
        first = self.app.test_client()
        self.log_in(first)
        first.post("/range/setup", data={"weapon": "M1911", "size": "s", "distance": "50"})
        second = self.app.test_client()
        second.post("/range/setup", data={"weapon": "M40A3", "size": "s", "distance": "50"})
        self.log_in(second)
        self.assertEqual(self.range_weapon(second), "M40A3")
        third = self.app.test_client()
        self.log_in(third)
        self.assertEqual(self.range_weapon(third), "M40A3")

    def test_a_second_account_on_the_same_browser_starts_without_the_first_ones_range(self):
        client = self.app.test_client()
        self.log_in(client, "1")
        client.post("/range/setup", data={"weapon": "M1911", "size": "s", "distance": "50"})
        client.post("/logout")
        self.log_in(client, "2")
        self.assertIsNone(self.range_weapon(client))

    def test_range_played_after_logging_out_joins_the_next_account(self):
        client = self.app.test_client()
        self.log_in(client, "1")
        client.post("/logout")
        client.post("/range/setup", data={"weapon": "AK47", "size": "s", "distance": "50"})
        self.log_in(client, "2")
        self.assertEqual(self.range_weapon(client), "AK47")

    def test_bad_callbacks_are_rejected(self):
        client = self.app.test_client()
        self.assertEqual(self.log_in(client, token=issue(aud="casino")).status_code, 400)
        self.assertEqual(client.post("/sso/callback", data={"state": "nope", "token": issue()}).status_code, 400)
        self.assertIn(b"Log in with portfolio account", client.get("/").data)


class PlayersTests(unittest.TestCase):
    def test_an_older_copy_never_replaces_a_newer_one(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            players = Players(os.path.join(folder, "players.db"))
            players.store("1", {"destroyed": 5}, saved_at=time.time())
            players.store("1", {"destroyed": 1}, saved_at=0)
            self.assertEqual(players.load("1")[0], {"destroyed": 5})


if __name__ == "__main__":
    unittest.main()
