import hashlib
import quopri
import re
from pathlib import Path

import pytest
import requests
from sqlalchemy import select

from app.database.models.user import User
from app.database.models.auth_token import AuthToken
from app.security.token_digest import token_digest
from app.security.passwords import password_hasher
from app.services.password_breach_service import PasswordBreachService, PASSWORD_REJECTED_MESSAGE


ACCOUNT = {"first_name": "Anna", "last_name": "Kowalska", "gender": "female", "birth_date": "1995-03-04",
           "phone": "+48123456789", "email": "anna@example.com", "password": "Bardzo unikalna fraza 2026!",
           "cat": {"name": "Mruczek", "gender": "unknown", "estimated_age_months": 8}}


class Response:
    def __init__(self, text=""):
        self.text = text

    def raise_for_status(self):
        return None


def enable(client):
    client.app.state.settings.password_breach_check_enabled = True
    PasswordBreachService._prefix_cache.clear()


def range_body(password, count=1):
    digest = hashlib.sha1(password.encode()).hexdigest().upper()
    return f"{digest[5:]}:{count}\r\n"


def test_safe_password_passes_breach_check(client, monkeypatch):
    enable(client)
    monkeypatch.setattr("app.services.password_breach_service.requests.get", lambda *args, **kwargs: Response())
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 201


def test_local_popular_password_is_rejected():
    class Settings:
        password_breach_check_enabled = False
    with pytest.raises(Exception) as error:
        PasswordBreachService(Settings()).validate("password")
    assert error.value.detail == PASSWORD_REJECTED_MESSAGE


def test_registration_rejects_breached_password(client, monkeypatch):
    enable(client)
    monkeypatch.setattr("app.services.password_breach_service.requests.get", lambda *args, **kwargs: Response(range_body(ACCOUNT["password"])))
    result = client.post("/api/auth/register", json=ACCOUNT)
    assert result.status_code == 422 and result.json()["detail"] == PASSWORD_REJECTED_MESSAGE
    with client.app.state.database.sessions() as db:
        assert db.scalar(select(User)) is None


def test_reset_rejects_breached_password_without_consuming_token(client, monkeypatch):
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 201
    assert client.post("/api/auth/forgot-password", json={"email": ACCOUNT["email"]}).status_code == 200
    content = quopri.decodestring(next(Path(client.app.state.settings.outbox_dir).glob("*.eml")).read_bytes()).decode()
    token = re.search(r"token=([A-Za-z0-9_-]+)", content).group(1)
    breached = "Nowa fraza z wycieku!"
    enable(client)
    monkeypatch.setattr("app.services.password_breach_service.requests.get", lambda *args, **kwargs: Response(range_body(breached)))
    assert client.post("/api/auth/reset-password", json={"token": token, "password": breached}).status_code == 422
    with client.app.state.database.sessions() as db:
        assert db.get(AuthToken, token_digest(token)) is not None
    client.app.state.settings.password_breach_check_enabled = False
    assert client.post("/api/auth/reset-password", json={"token": token, "password": "Nowa unikalna fraza 2026!"}).status_code == 200


def test_login_does_not_call_breach_service(client, monkeypatch):
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 201
    enable(client)
    monkeypatch.setattr("app.services.password_breach_service.requests.get", lambda *args, **kwargs: pytest.fail("login called breach service"))
    assert client.post("/api/auth/login", json={"email": ACCOUNT["email"], "password": ACCOUNT["password"]}).status_code == 200


def test_only_sha1_prefix_leaves_backend(client, monkeypatch):
    enable(client)
    seen = {}
    password = ACCOUNT["password"]
    digest = hashlib.sha1(password.encode()).hexdigest().upper()

    def fake_get(url, **kwargs):
        seen.update(url=url, kwargs=kwargs)
        return Response()

    monkeypatch.setattr("app.services.password_breach_service.requests.get", fake_get)
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 201
    assert seen["url"].endswith("/" + digest[:5])
    assert password not in seen["url"] and digest not in seen["url"]
    assert seen["kwargs"]["timeout"] == 2.0


def test_breach_timeout_keeps_local_policy_and_argon2(client, monkeypatch, caplog):
    enable(client)
    monkeypatch.setattr("app.services.password_breach_service.requests.get", lambda *args, **kwargs: (_ for _ in ()).throw(requests.Timeout()))
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 201
    with client.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")
        assert password_hasher.verify(ACCOUNT["password"], user.password_hash)
    digest = hashlib.sha1(ACCOUNT["password"].encode()).hexdigest().upper()
    assert ACCOUNT["password"] not in caplog.text and digest not in caplog.text
