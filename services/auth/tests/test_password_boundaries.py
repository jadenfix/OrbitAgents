"""Regression coverage for exact UTF-8 bcrypt boundaries and HTTP secrecy."""

import importlib
import secrets
import string

import bcrypt
import pytest

from schemas import UserLogin

_auth = importlib.import_module("main")


def boundary_password(multibyte=False):
    prefix = "".join(
        secrets.choice(category)
        for category in (
            string.ascii_uppercase,
            string.ascii_lowercase,
            string.digits,
            string.punctuation,
        )
    )
    suffix = (
        "🔐🚀" * 8 + secrets.token_urlsafe(3)
        if multibyte
        else secrets.token_urlsafe(51)
    )
    password = prefix + suffix
    assert len(password.encode("utf-8")) == 72
    return password


@pytest.mark.parametrize("multibyte", [False, True])
def test_actual_http_rejects_shared_prefix_password_variants(client, multibyte):
    password = boundary_password(multibyte)
    email = secrets.token_hex(8) + "@example.com"
    credential = {"email": email, "password": password}
    assert client.post("/register", json=credential).status_code == 201
    assert client.post("/login", json=credential).status_code == 200
    for variant in [password + secrets.token_urlsafe(1), password + "é"]:
        assert variant != password
        for route in ["/register", "/login"]:
            response = client.post(route, json={**credential, "password": variant})
            assert response.status_code == 422
            assert variant not in response.text
            assert password not in response.text
            assert all(
                "input" not in error and "ctx" not in error
                for error in response.json()["errors"]
            )
    assert client.post("/login", json=credential).status_code == 200


@pytest.mark.parametrize("multibyte", [False, True])
def test_direct_hash_and_verify_never_truncate(multibyte):
    password = boundary_password(multibyte)
    hashed = _auth.hash_password(password)
    assert _auth.verify_password(password, hashed)
    # Even callers bypassing the HTTP schemas cannot authenticate a shared prefix.
    for variant in [password + "a", password + "é"]:
        assert not _auth.verify_password(variant, hashed)
        with pytest.raises(ValueError, match="72 UTF-8 bytes"):
            _auth.hash_password(variant)
    assert not _auth.verify_password(password, "malformed")


@pytest.mark.parametrize("prefix", [b"2a", b"2b"])
def test_existing_standard_bcrypt_hashes_still_verify(prefix):
    password = boundary_password()
    old_format = bcrypt.hashpw(
        password.encode(), bcrypt.gensalt(rounds=12, prefix=prefix)
    )
    assert _auth.verify_password(password, old_format.decode())
    assert not _auth.verify_password(password[:-1], old_format.decode())


def test_password_whitespace_is_not_silently_normalized(client):
    password = boundary_password()[:32]
    credential = {"email": secrets.token_hex(8) + "@example.com", "password": password}
    assert client.post("/register", json=credential).status_code == 201
    assert client.post("/login", json=credential).status_code == 200
    assert (
        client.post(
            "/login", json={**credential, "password": " " + password}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/register", json={**credential, "password": " " + password}
        ).status_code
        == 422
    )
    assert (
        UserLogin(**{**credential, "password": " " + password}).password
        == " " + password
    )
