import base64
import os
import tempfile
import time
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from webapp import create_app

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = base64.b64encode(KEY.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)).decode()


def issue(sub="1", name="ronovo", aud="gunsystem"):
    now = int(time.time())
    return jwt.encode({"iss": "portfolio", "aud": aud, "sub": sub, "name": name, "iat": now, "exp": now + 300},
                      KEY, algorithm="RS256")


class PortfolioOffTests(unittest.TestCase):
    def test_no_portfolio_login_without_config(self):
        with mock.patch.dict(os.environ, {"PORTFOLIO_SSO_URL": "", "PORTFOLIO_SSO_PUBLIC_KEY": ""}):
            client = create_app({"TESTING": True, "SECRET_KEY": "test"}).test_client()
        self.assertNotIn(b"Log in with portfolio account", client.get("/").data)
        self.assertEqual(client.get("/sso/login").status_code, 404)


class PortfolioLoginTests(unittest.TestCase):
    def setUp(self):
        data_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(data_dir.cleanup)
        env = mock.patch.dict(os.environ, {"PORTFOLIO_SSO_URL": "http://portfolio.test", "PORTFOLIO_SSO_PUBLIC_KEY": PUBLIC_KEY})
        env.start()
        self.addCleanup(env.stop)
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test", "DATA_DIR": data_dir.name})

    def log_in(self, client, sub="1", token=None):
        location = client.get("/sso/login").location
        query = parse_qs(urlsplit(location).query)
        self.assertEqual(query["app"], ["gunsystem"])
        return client.post("/sso/callback", data={"state": query["state"][0], "token": token or issue(sub)})

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
        for _ in range(40):
            first.post("/range/fire")
            first.post("/range/reload")
        with first.session_transaction() as session:
            destroyed = session.get("destroyed", 0)

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

    def test_bad_callbacks_are_rejected(self):
        client = self.app.test_client()
        self.assertEqual(self.log_in(client, token=issue(aud="casino")).status_code, 400)
        self.assertEqual(client.post("/sso/callback", data={"state": "nope", "token": issue()}).status_code, 400)
        self.assertIn(b"Log in with portfolio account", client.get("/").data)


if __name__ == "__main__":
    unittest.main()
