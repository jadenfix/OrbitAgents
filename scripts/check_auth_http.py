#!/usr/bin/env python3
"""Real loopback HTTP registration/login with SQLite persistence; no provider mocks."""

import json
import os
import secrets
import string
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def temporary_password() -> str:
    categories = (
        string.ascii_uppercase,
        string.ascii_lowercase,
        string.digits,
        string.punctuation,
    )
    return "".join(
        secrets.choice(category) for category in categories
    ) + secrets.token_urlsafe(24)


def main():
    with tempfile.TemporaryDirectory() as temporary:
        db = Path(temporary) / "auth.sqlite"
        env = os.environ.copy()
        env.update(
            DATABASE_URL=f"sqlite:///{db}",
            JWT_SECRET=secrets.token_urlsafe(48),
            RATE_LIMIT_ENABLED="false",
        )
        for key in list(env):
            if key.lower().endswith("proxy"):
                env.pop(key)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def request(path, payload=None, token=None):
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = "Bearer " + token
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=json.dumps(payload).encode() if payload is not None else None,
                headers=headers,
            )
            try:
                with opener.open(req, timeout=5) as response:
                    return response.status, json.loads(response.read())
            except urllib.error.HTTPError as error:
                return error.code, json.loads(error.read())

        credentials = {
            "email": "http-fixture@example.com",
            "password": temporary_password(),
        }
        # Two distinct over-budget passwords shared bcrypt's first 72 bytes.
        # Neither may authenticate, even across the real server/database restart.
        boundary_password = "".join(
            secrets.choice(category)
            for category in (
                string.ascii_uppercase,
                string.ascii_lowercase,
                string.digits,
                string.punctuation,
            )
        ) + secrets.token_urlsafe(51)
        assert len(boundary_password.encode("utf-8")) == 72
        boundary_credentials = {
            "email": "boundary-fixture@example.com",
            "password": boundary_password,
        }
        oversized_passwords = [
            boundary_password + secrets.token_urlsafe(1),
            boundary_password + "é",
        ]
        assert oversized_passwords[0] != oversized_passwords[1]
        multibyte_password = (
            temporary_password()[:4] + "🔐🚀" * 8 + secrets.token_urlsafe(3)
        )
        assert len(multibyte_password.encode("utf-8")) == 72
        assert len(multibyte_password) < 72
        multibyte_credentials = {
            "email": "multibyte-fixture@example.com",
            "password": multibyte_password,
        }
        boundary_cases = [
            (boundary_credentials, oversized_passwords),
            (
                multibyte_credentials,
                [multibyte_password + "é", multibyte_password + "a"],
            ),
        ]
        for iteration in range(2):
            with open(Path(temporary) / "server.log", "a+") as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                    ],
                    cwd=ROOT / "services/auth",
                    env=env,
                    stdout=log,
                    stderr=log,
                )
                try:
                    for attempt in range(150):
                        if process.poll() is not None:
                            log.seek(0)
                            raise RuntimeError(log.read())
                        try:
                            if request("/healthz")[0] == 200:
                                break
                        except (OSError, urllib.error.URLError):
                            time.sleep(0.1)
                    else:
                        raise RuntimeError("Auth HTTP startup timed out")
                    if iteration == 0:
                        assert request("/register", credentials)[0] == 201
                        for boundary, variants in boundary_cases:
                            assert request("/register", boundary)[0] == 201
                            for password in variants:
                                status, response = request(
                                    "/register", {**boundary, "password": password}
                                )
                                assert status == 422
                                assert password not in json.dumps(response)
                                assert boundary["password"] not in json.dumps(response)
                        assert request("/register", credentials)[0] == 400
                        assert (
                            request("/register", {"email": "bad", "password": "short"})[
                                0
                            ]
                            == 422
                        )
                    for boundary, variants in boundary_cases:
                        for password in variants:
                            status, response = request(
                                "/login", {**boundary, "password": password}
                            )
                            assert status == 422
                            assert password not in json.dumps(response)
                            assert boundary["password"] not in json.dumps(response)
                        assert request("/login", boundary)[0] == 200
                    status, login = request("/login", credentials)
                    assert status == 200, login
                    assert (
                        request("/me", token=login["access_token"])[1]["email"]
                        == credentials["email"]
                    )
                    assert (
                        request(
                            "/login",
                            {
                                **credentials,
                                "password": temporary_password(),
                            },
                        )[0]
                        == 401
                    )
                    assert request("/me", token="invalid-token")[0] == 401
                finally:
                    process.terminate()
                    process.wait(timeout=10)
        with sqlite3.connect(db) as connection:
            row = connection.execute(
                "select email, hashed_password from users"
            ).fetchone()
            assert row[0] == credentials["email"]
            assert row[1] != credentials["password"] and row[1].startswith("$2")
        server_log = (Path(temporary) / "server.log").read_text()
        assert credentials["password"] not in server_log
        for boundary, variants in boundary_cases:
            assert boundary["password"] not in server_log
            assert all(password not in server_log for password in variants)
        print(
            "PASS: real HTTP registration, validation, JWT login, rejected login, hashed SQLite persistence, 72-byte shared-prefix rejection, secret-safe errors/logs, and restart"
        )


if __name__ == "__main__":
    main()
