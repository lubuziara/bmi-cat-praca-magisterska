import base64
import hashlib
import hmac
import re
import secrets
import struct
import time

from sqlalchemy import func, select

from app.database.models.access_token import AccessToken
from app.database.models.auth_token import AuthToken
from app.database.models.user_mfa import MfaChallenge, RecoveryCode, UserMfa
from app.database.models.refresh_token import RefreshToken
from app.database.models.user import User
from app.security.token_digest import token_digest
from tests.test_auth import ACCOUNT


def code(secret):
    counter = int(time.time()) // 30
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    return f"{(struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7fffffff) % 1000000:06d}"


def enable(client):
    created = client.post("/api/auth/register", json=ACCOUNT).json()
    bearer = {"Authorization": f"Bearer {created['access_token']}"}
    setup = client.post("/api/auth/2fa/setup", headers=bearer, json={"password": ACCOUNT["password"]}).json()
    secret = re.search(r"secret=([^&]+)", setup["otpauth_uri"]).group(1)
    confirmed = client.post("/api/auth/2fa/confirm", headers=bearer,
                            json={"setup_challenge": setup["setup_challenge"], "code": code(secret)})
    assert confirmed.status_code == 200
    return secret, confirmed.json()["recovery_codes"], bearer


def login_challenge(client, headers=None):
    result = client.post("/api/auth/login", json=ACCOUNT, headers=headers or {})
    assert result.status_code == 200 and result.json()["mfa_required"] is True
    return result.json()["mfa_challenge"]


def test_setup_does_not_enable_2fa(client):
    created = client.post("/api/auth/register", json=ACCOUNT).json()
    bearer = {"Authorization": f"Bearer {created['access_token']}"}
    assert client.post("/api/auth/2fa/setup", headers=bearer, json={"password": ACCOUNT["password"]}).status_code == 200
    assert client.get("/api/auth/2fa/status", headers=bearer).json() == {"enabled": False}


def test_bad_setup_code_does_not_enable_2fa(client):
    created = client.post("/api/auth/register", json=ACCOUNT).json()
    bearer = {"Authorization": f"Bearer {created['access_token']}"}
    setup = client.post("/api/auth/2fa/setup", headers=bearer, json={"password": ACCOUNT["password"]}).json()
    assert client.post("/api/auth/2fa/confirm", headers=bearer,
                       json={"setup_challenge": setup["setup_challenge"], "code": "000000"}).status_code == 401
    assert client.get("/api/auth/2fa/status", headers=bearer).json() == {"enabled": False}


def test_correct_setup_code_enables_2fa(client):
    _, _, bearer = enable(client)
    assert client.get("/api/auth/2fa/status", headers=bearer).json() == {"enabled": True}


def test_mfa_login_does_not_create_session_before_second_factor(client):
    enable(client)
    with client.app.state.database.sessions() as db:
        before = db.scalar(select(func.count()).select_from(AccessToken))
    result = client.post("/api/auth/login", json=ACCOUNT)
    assert "access_token" not in result.json() and "refresh_token" not in result.json()
    with client.app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(AccessToken)) == before


def test_correct_totp_completes_login(client):
    secret, _, _ = enable(client)
    result = client.post("/api/auth/2fa/verify", json={"mfa_challenge": login_challenge(client), "code": code(secret)})
    assert result.status_code == 200 and result.json()["access_token"] and result.json()["refresh_token"]


def test_bad_totp_does_not_create_session(client):
    enable(client)
    with client.app.state.database.sessions() as db:
        before = db.scalar(select(func.count()).select_from(AccessToken))
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": login_challenge(client), "code": "000000"}).status_code == 401
    with client.app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(AccessToken)) == before


def test_challenge_expires_and_is_single_use(client):
    secret, _, _ = enable(client)
    challenge = login_challenge(client)
    with client.app.state.database.sessions() as db:
        db.get(MfaChallenge, token_digest(challenge)).expires_at = int(time.time()) - 1
        db.commit()
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": challenge, "code": code(secret)}).status_code == 401
    challenge = login_challenge(client)
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": challenge, "code": code(secret)}).status_code == 200
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": challenge, "code": code(secret)}).status_code == 401


def test_same_totp_cannot_be_reused_in_window(client):
    secret, _, _ = enable(client)
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": login_challenge(client), "code": code(secret)}).status_code == 200
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": login_challenge(client), "code": code(secret)}).status_code == 401


def test_recovery_code_works_once(client):
    _, recovery, _ = enable(client)
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": login_challenge(client), "code": recovery[0]}).status_code == 200
    step_up = client.post("/api/auth/login", json=ACCOUNT).json()
    assert step_up["step_up_required"] is True
    assert client.post("/api/auth/step-up/verify", json={"step_up_challenge": step_up["step_up_challenge"], "code": recovery[0]}).status_code == 401


def test_regeneration_invalidates_old_recovery_codes(client):
    secret, recovery, bearer = enable(client)
    regenerated = client.post("/api/auth/2fa/recovery/regenerate", headers=bearer,
                              json={"password": ACCOUNT["password"], "code": code(secret)})
    assert regenerated.status_code == 200 and recovery[0] not in regenerated.json()["recovery_codes"]
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": login_challenge(client), "code": recovery[0]}).status_code == 401


def test_mfa_rate_limit_blocks_excessive_attempts(client):
    enable(client)
    challenge = login_challenge(client)
    for _ in range(5):
        assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": challenge, "code": "000000"}).status_code == 401
    assert client.post("/api/auth/2fa/verify", json={"mfa_challenge": challenge, "code": "000000"}).status_code == 429


def test_web_has_no_refresh_cookie_before_mfa(client):
    enable(client)
    result = client.post("/api/auth/login", json=ACCOUNT, headers={"X-BMI-Client": "web"})
    assert result.json()["mfa_required"] is True and not result.headers.get_list("set-cookie")


def test_web_sets_session_after_mfa(client):
    secret, _, _ = enable(client)
    headers = {"X-BMI-Client": "web"}
    result = client.post("/api/auth/2fa/verify", headers=headers,
                         json={"mfa_challenge": login_challenge(client, headers), "code": code(secret)})
    assert "refresh_token" not in result.json()
    assert any("bmi_refresh=" in value and "HttpOnly" in value for value in result.headers.get_list("set-cookie"))


def test_password_reset_does_not_disable_2fa(client):
    enable(client)
    with client.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        assert db.get(UserMfa, user.id).enabled is True
        raw = secrets.token_urlsafe(32)
        db.add(AuthToken(digest=token_digest(raw), user_id=user.id, purpose="reset", expires_at=int(time.time()) + 60))
        db.commit()
    assert client.post("/api/auth/reset-password", json={"token": raw, "password": "Nowa bezpieczna fraza!"}).status_code == 200
    with client.app.state.database.sessions() as db:
        assert db.get(UserMfa, user.id).enabled is True


def test_google_account_requires_fresh_matching_google_token_for_reauth(client, monkeypatch):
    secret, _, bearer = enable(client)
    with client.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        user.password_hash = None
        user.google_subject = "subject"
        db.commit()
    client.app.state.settings.google_client_id = "client"
    monkeypatch.setattr("app.services.google_auth_service.id_token.verify_oauth2_token", lambda token, *args: {"sub": token, "email_verified": True, "iat": int(time.time())})
    payload = {"code": code(secret)}
    assert client.post("/api/auth/2fa/recovery/regenerate", headers=bearer, json=payload).status_code == 401
    assert client.post("/api/auth/2fa/recovery/regenerate", headers=bearer,
                       json={**payload, "google_id_token": "other"}).status_code == 401
    assert client.post("/api/auth/2fa/recovery/regenerate", headers=bearer,
                       json={**payload, "google_id_token": "subject"}).status_code == 200
