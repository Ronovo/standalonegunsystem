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
from flask import Flask

from webapp import create_app

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = base64.b64encode(KEY.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)).decode()


def issue(sub="1", name="ronovo", aud="gunsystem"):
    now = int(time.time())
    return jwt.encode({"iss": "portfolio", "aud": aud, "sub": sub, "name": name, "iat": now, "exp": now + 300},
                      KEY, algorithm="RS256")


def make_app(test: unittest.TestCase, portfolio: bool = False) -> Flask:
    """An app with its own temporary data folder. Portfolio login is on only when asked for, whatever the shell
    running the tests has set."""
    data_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    test.addCleanup(data_dir.cleanup)
    env = mock.patch.dict(os.environ, {"PORTFOLIO_SSO_URL": "http://portfolio.test" if portfolio else "",
                                       "PORTFOLIO_SSO_PUBLIC_KEY": PUBLIC_KEY if portfolio else ""})
    env.start()
    test.addCleanup(env.stop)
    return create_app({"TESTING": True, "SECRET_KEY": "test", "DATA_DIR": data_dir.name})


def log_in(client, sub="1", token=None):
    query = parse_qs(urlsplit(client.get("/sso/login").location).query)
    assert query["app"] == ["gunsystem"]
    return client.post("/sso/callback", data={"state": query["state"][0], "token": token or issue(sub)})
