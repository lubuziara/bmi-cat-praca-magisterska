import re
import time
from pathlib import Path
import pytest
from sqlalchemy import select
from app.database.models.user import User
from app.database.models.auth_token import AuthToken
from app.database.models.access_token import AccessToken
from app.database.models.refresh_token import RefreshToken
from app.security.token_digest import token_digest
from app.security.passwords import password_hasher
from app.config import Settings

ACCOUNT = {"first_name": "Anna-Maria", "last_name": "Kowalska", "gender": "female", "birth_date": "1995-04-12", "phone": "+48123456789", "cat": {"name": "Mruczek", "gender": "male", "estimated_age_months": 12}, "email": "anna@example.com", "password": "Dluga fraza haslowa 123!"}


def test_register_login_me_logout(client):
    created = client.post("/api/auth/register", json=ACCOUNT)
    assert created.status_code == 201
    with client.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")
        assert password_hasher.verify(ACCOUNT["password"], user.password_hash)
    response = client.post("/api/auth/login", json=ACCOUNT)
    assert response.status_code == 200
    raw = response.json()["access_token"]
    refresh = response.json()["refresh_token"]
    assert response.json()["expires_in"] == 900
    headers = {"Authorization": f"Bearer {raw}"}
    with client.app.state.database.sessions() as db:
        token = db.get(AccessToken, token_digest(raw))
        assert token.digest == token_digest(raw) and token.digest != raw
        stored_refresh = db.get(RefreshToken, token_digest(refresh))
        assert stored_refresh.digest == token_digest(refresh) and stored_refresh.digest != refresh
    me = client.get("/api/auth/me", headers=headers)
    assert me.json()["first_name"] == "Anna-Maria"
    assert "password" not in str(me.json())
    assert me.headers["cache-control"] == "no-store"
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


@pytest.mark.parametrize("name", ["666", "Anna123", "<script>", "", "   ", "A" * 81])
def test_invalid_name_rejected(client, name):
    assert client.post("/api/auth/register", json={**ACCOUNT, "first_name": name}).status_code == 422


@pytest.mark.parametrize("name", ["Łucja", "O’Connor", "李", "Anne Marie"])
def test_international_names_accepted(client, name):
    assert client.post("/api/auth/register", json={**ACCOUNT, "first_name": name}).status_code == 201


@pytest.mark.parametrize("field,value", [("email", "invalid"), ("email", "a@"), ("password", "short"), ("password", "x" * 129)])
def test_registration_validation(client, field, value):
    assert client.post("/api/auth/register", json={**ACCOUNT, field: value}).status_code == 422


def test_email_normalization_duplicate(client):
    assert client.post("/api/auth/register", json={**ACCOUNT, "email": " Anna@Example.COM "}).status_code == 201
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 409
    assert client.post("/api/auth/login", json=ACCOUNT).status_code == 200


def test_login_errors_do_not_reveal_account(client):
    client.post("/api/auth/register", json=ACCOUNT)
    wrong = client.post("/api/auth/login", json={**ACCOUNT, "password": "wrong"})
    unknown = client.post("/api/auth/login", json={**ACCOUNT, "email": "unknown@example.com"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    injection = client.post("/api/auth/login", json={**ACCOUNT, "email": "' OR 1=1 --"})
    assert injection.status_code == 422


def test_requires_valid_session_and_expiry(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer made-up"}).status_code == 401
    client.post("/api/auth/register", json=ACCOUNT)
    raw = client.post("/api/auth/login", json=ACCOUNT).json()["access_token"]
    with client.app.state.database.sessions() as db:
        db.get(AccessToken, token_digest(raw)).expires_at = int(time.time()) - 1
        db.commit()
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {raw}"}).status_code == 401


def test_reset_single_use_and_session_revocation(client):
    client.post("/api/auth/register", json=ACCOUNT)
    session = client.post("/api/auth/login", json=ACCOUNT).json()["access_token"]
    known = client.post("/api/auth/forgot-password", json=ACCOUNT)
    unknown = client.post("/api/auth/forgot-password", json={"email": "missing@example.com"})
    assert known.status_code == unknown.status_code == 200 and known.json() == unknown.json()
    messages = list(Path(client.app.state.settings.outbox_dir).glob("*.eml"))
    assert len(messages) == 1
    # Odczyt MIME usuwa ewentualne zawijanie quoted-printable.
    from email import policy
    from email.parser import BytesParser
    content = BytesParser(policy=policy.default).parsebytes(messages[0].read_bytes()).get_content()
    raw = re.search(r"token=([A-Za-z0-9_-]+)", content).group(1)
    assert raw not in known.text
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {raw}"}).status_code == 401
    payload = {"token": raw, "password": "Nowa bezpieczna fraza!"}
    assert client.post("/api/auth/reset-password", json=payload).status_code == 200
    assert client.post("/api/auth/reset-password", json=payload).status_code == 400
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {session}"}).status_code == 401
    assert client.post("/api/auth/login", json=ACCOUNT).status_code == 401
    assert client.post("/api/auth/login", json={**ACCOUNT, "password": payload["password"]}).status_code == 200


def test_refresh_rotates_and_reuse_revokes_session_family(client):
    client.post("/api/auth/register", json=ACCOUNT)
    login = client.post("/api/auth/login", json=ACCOUNT).json()
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refreshed.status_code == 200
    next_tokens = refreshed.json()
    assert next_tokens["refresh_token"] != login["refresh_token"]
    assert next_tokens["expires_in"] == 900
    assert next_tokens["refresh_expires_in"] == 60 * 60 * 24 * 30
    assert client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {next_tokens['access_token']}"}).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": next_tokens["refresh_token"]}).status_code == 401


def test_web_session_uses_httponly_refresh_cookie_and_csrf(client):
    client.post("/api/auth/register", json=ACCOUNT)
    web_headers = {"X-BMI-Client": "web"}
    login = client.post("/api/auth/login", json=ACCOUNT, headers=web_headers)
    assert login.status_code == 200
    assert "refresh_token" not in login.json()
    refresh_cookie = login.headers.get_list("set-cookie")[0]
    csrf_cookie = login.headers.get_list("set-cookie")[1]
    assert "bmi_refresh=" in refresh_cookie and "HttpOnly" in refresh_cookie
    assert "SameSite=lax" in refresh_cookie and "Path=/api/auth" in refresh_cookie
    assert "Secure" not in refresh_cookie
    assert "bmi_csrf=" in csrf_cookie and "HttpOnly" not in csrf_cookie

    assert client.post("/api/auth/refresh", headers=web_headers).status_code == 403
    csrf = client.cookies.get("bmi_csrf")
    refreshed = client.post("/api/auth/refresh", headers={**web_headers, "X-CSRF-Token": csrf})
    assert refreshed.status_code == 200
    assert "refresh_token" not in refreshed.json()
    assert client.cookies.get("bmi_refresh")


def test_cookie_secure_defaults_to_true_and_cors_wildcard_is_rejected():
    assert Settings(_env_file=None).cookie_secure is True
    with pytest.raises(ValueError):
        Settings(cors_origins=["*"], _env_file=None)


def test_web_logout_requires_csrf_revokes_family_and_clears_cookie(client):
    client.post("/api/auth/register", json=ACCOUNT)
    web_headers = {"X-BMI-Client": "web"}
    client.post("/api/auth/login", json=ACCOUNT, headers=web_headers)
    csrf = client.cookies.get("bmi_csrf")
    assert client.post("/api/auth/logout", headers=web_headers).status_code == 403
    logout = client.post("/api/auth/logout", headers={**web_headers, "X-CSRF-Token": csrf})
    assert logout.status_code == 200
    assert any("bmi_refresh=\"\"" in value and "Max-Age=0" in value for value in logout.headers.get_list("set-cookie"))


def test_logout_revokes_only_current_session_family(client):
    client.post("/api/auth/register", json=ACCOUNT)
    first = client.post("/api/auth/login", json=ACCOUNT).json()
    second = client.post("/api/auth/login", json=ACCOUNT).json()
    assert client.post("/api/auth/logout", headers={"Authorization": f"Bearer {first['access_token']}"}).status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": first["refresh_token"]}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {second['access_token']}"}).status_code == 200


def test_expired_reset_and_session_cannot_reset_password(client):
    client.post("/api/auth/register", json=ACCOUNT)
    raw = client.post("/api/auth/login", json=ACCOUNT).json()["access_token"]
    assert client.post("/api/auth/reset-password", json={"token": raw, "password": "Nowa dluga fraza!"}).status_code == 400
    with client.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        db.add(AuthToken(digest=token_digest(raw), user_id=user.id, purpose="reset",
                         expires_at=int(time.time()) - 1))
        db.commit()
    assert client.post("/api/auth/reset-password", json={"token": raw, "password": "Nowa dluga fraza!"}).status_code == 400


def test_rate_limit(client):
    for _ in range(10):
        assert client.post("/api/auth/login", json=ACCOUNT).status_code == 401
    response = client.post("/api/auth/login", json=ACCOUNT)
    assert response.status_code == 429 and 1 <= int(response.headers["retry-after"]) <= 60


def test_cors(client):
    good = client.options("/api/auth/login", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert good.headers["access-control-allow-origin"] == "http://localhost:5173"
    bad = client.options("/api/auth/login", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers


def test_google_disabled(client):
    assert client.post("/api/auth/google", json={"id_token": "bad"}).status_code == 503


def test_google_checks_identity_and_does_not_link_by_email(client, monkeypatch):
    client.app.state.settings.google_client_id = "test-client"
    def verify(token, request, audience):
        assert audience == "test-client"
        if token == "bad": raise ValueError()
        return {"sub": "google-user", "email": ACCOUNT["email"], "email_verified": token != "unverified", "given_name": "Anna"}
    monkeypatch.setattr("app.services.google_auth_service.id_token.verify_oauth2_token", verify)
    assert client.post("/api/auth/google", json={"id_token": "bad"}).status_code == 401
    assert client.post("/api/auth/google", json={"id_token": "unverified"}).status_code == 401
    client.post("/api/auth/register", json=ACCOUNT)
    assert client.post("/api/auth/google", json={"id_token": "verified"}).status_code == 409


def test_google_creates_session_for_verified_identity(client, monkeypatch):
    client.app.state.settings.google_client_id = "test-client"
    monkeypatch.setattr("app.services.google_auth_service.id_token.verify_oauth2_token", lambda *args: {"sub": "123", "email": "google@example.com", "email_verified": True, "given_name": "Anna"})
    first = client.post("/api/auth/google", json={"id_token": "verified"})
    second = client.post("/api/auth/google", json={"id_token": "verified"})
    assert first.status_code == second.status_code == 200
    assert first.json()["user"]["id"] == second.json()["user"]["id"]


def test_validation_does_not_echo_password(client):
    result = client.post("/api/auth/register", json={**ACCOUNT, "password": "secret"})
    assert result.status_code == 422
    assert "secret" not in result.text
