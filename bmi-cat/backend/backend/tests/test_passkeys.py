import base64
import json
import time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.database.models.passkey import Passkey, PasskeyChallenge
from app.database.models.user import User
from app.security.token_digest import token_digest
from app.services.passkey_service import PasskeyService
from tests.test_auth import ACCOUNT


def b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def credential(challenge, raw_id=b"credential-1", origin="http://localhost:5173"):
    client_data = b64(json.dumps({"type": "webauthn.create", "challenge": b64(challenge), "origin": origin}).encode())
    return {"rawId": b64(raw_id), "response": {"clientDataJSON": client_data}}


def setup(client):
    client.app.state.settings.webauthn_rp_id = "localhost"
    client.app.state.settings.webauthn_origin = "http://localhost:5173"
    registered = client.post("/api/auth/register", json=ACCOUNT).json()
    return {"Authorization": "Bearer " + registered["access_token"]}


def service(client):
    return PasskeyService(client.app.state.database.sessions(), client.app.state.settings)


def test_registration_challenges_are_random_and_hashed(client):
    headers = setup(client)
    first = client.post("/api/auth/passkeys/register/options", headers=headers, json={"password": ACCOUNT["password"]}).json()["challenge"]
    second = client.post("/api/auth/passkeys/register/options", headers=headers, json={"password": ACCOUNT["password"]}).json()["challenge"]
    assert first != second
    with client.app.state.database.sessions() as db:
        assert db.get(PasskeyChallenge, token_digest(first)) is not None
        assert first not in [row.digest for row in db.scalars(select(PasskeyChallenge))]


def test_challenge_expiry_kind_and_single_use(client):
    setup(client); svc = service(client); raw = svc._issue(1, "register")
    data = credential(raw)
    svc._consume(data, "register", 1)
    with pytest.raises(HTTPException): svc._consume(data, "register", 1)
    other = svc._issue(1, "register")
    with pytest.raises(HTTPException): svc._consume(credential(other), "login")
    expired = svc._issue(1, "register")
    record = svc.session.get(PasskeyChallenge, token_digest(b64(expired))); record.expires_at = int(time.time()) - 1; svc.session.commit()
    with pytest.raises(HTTPException): svc._consume(credential(expired), "register", 1)


def test_tampered_challenge_is_rejected(client):
    setup(client); svc = service(client); raw = svc._issue(1, "login")
    with pytest.raises(HTTPException): svc._consume(credential(raw + b"x"), "login")


def test_invalid_server_origin_or_rp_configuration_is_rejected(client):
    setup(client); svc = service(client)
    client.app.state.settings.webauthn_origin = "http://evil.example"
    with pytest.raises(HTTPException): svc.login_options()
    client.app.state.settings.webauthn_origin = "https://localhost:5173"
    client.app.state.settings.webauthn_rp_id = "evil.example"
    with pytest.raises(HTTPException): svc.login_options()


def test_registration_passes_server_config_and_rejects_invalid_origin(client, monkeypatch):
    headers = setup(client)
    options = client.post("/api/auth/passkeys/register/options", headers=headers, json={"password": ACCOUNT["password"]}).json()
    seen = {}
    def reject(**kwargs):
        seen.update(kwargs)
        if kwargs["credential"]["response"]["clientDataJSON"]:
            raise ValueError("invalid origin")
    monkeypatch.setattr("app.services.passkey_service.verify_registration_response", reject)
    response = client.post("/api/auth/passkeys/register/verify", headers=headers, json={"credential": credential(base64.urlsafe_b64decode(options["challenge"] + "=="), origin="https://evil.example")})
    assert response.status_code == 401
    assert seen["expected_rp_id"] == "localhost" and "http://localhost:5173" in seen["expected_origin"]


def test_registration_saves_only_public_credential_data_and_allows_many(client, monkeypatch):
    headers = setup(client)
    monkeypatch.setattr("app.services.passkey_service.verify_registration_response", lambda **kw: SimpleNamespace(credential_id=_raw_id(kw["credential"]), credential_public_key=b"public-key", sign_count=0))
    for raw_id in (b"first", b"second"):
        options = client.post("/api/auth/passkeys/register/options", headers=headers, json={"password": ACCOUNT["password"]}).json()
        response = client.post("/api/auth/passkeys/register/verify", headers=headers, json={"credential": credential(base64.urlsafe_b64decode(options["challenge"] + "=="), raw_id)})
        assert response.status_code == 200
    with client.app.state.database.sessions() as db:
        keys = db.scalars(select(Passkey)).all()
        assert len(keys) == 2 and all(key.public_key == b"public-key" for key in keys)
        assert all("private" not in column.name for column in Passkey.__table__.columns)


def _raw_id(value):
    return base64.urlsafe_b64decode(value["rawId"] + "=" * (-len(value["rawId"]) % 4))


def test_credential_cannot_be_reassigned_to_another_user(client, monkeypatch):
    headers = setup(client); svc = service(client)
    monkeypatch.setattr("app.services.passkey_service.verify_registration_response", lambda **kw: SimpleNamespace(credential_id=b"shared", credential_public_key=b"pub", sign_count=0))
    first = svc._issue(1, "register"); svc.registration_verify(svc.session.get(User, 1), credential(first))
    user = User(email="second@example.com", first_name="Second", password_hash="hash"); svc.session.add(user); svc.session.commit()
    second = svc._issue(user.id, "register")
    with pytest.raises(HTTPException) as error: svc.registration_verify(user, credential(second))
    assert error.value.status_code == 409


def test_login_uses_session_and_blocks_bad_signature_and_replay(client, monkeypatch):
    headers = setup(client)
    with client.app.state.database.sessions() as db:
        db.add(Passkey(user_id=1, credential_id=b"login", public_key=b"pub", sign_count=0, created_at=1)); db.commit()
    options = client.post("/api/auth/passkeys/login/options").json()
    data = credential(base64.urlsafe_b64decode(options["challenge"] + "=="), b"login")
    monkeypatch.setattr("app.services.passkey_service.verify_authentication_response", lambda **kw: SimpleNamespace(new_sign_count=0))
    success = client.post("/api/auth/passkeys/login/verify", json={"credential": data})
    assert success.status_code == 200 and "access_token" in success.json()
    assert client.post("/api/auth/passkeys/login/verify", json={"credential": data}).status_code == 401
    options = client.post("/api/auth/passkeys/login/options").json()
    monkeypatch.setattr("app.services.passkey_service.verify_authentication_response", lambda **kw: (_ for _ in ()).throw(ValueError("bad signature")))
    assert client.post("/api/auth/passkeys/login/verify", json={"credential": credential(base64.urlsafe_b64decode(options["challenge"] + "=="), b"login")}).status_code == 401


def test_delete_requires_reauth_and_prevents_idor_and_lockout(client, monkeypatch):
    headers = setup(client)
    with client.app.state.database.sessions() as db:
        db.add(Passkey(user_id=1, credential_id=b"one", public_key=b"pub", sign_count=0, created_at=1)); db.commit()
        key_id = db.scalar(select(Passkey.id))
    assert client.request("DELETE", f"/api/auth/passkeys/{key_id}", headers=headers, json={"password": "wrong", "code": "123456"}).status_code == 401
    monkeypatch.setattr("app.services.auth_service.AuthService._require_reauthentication", lambda *args: None)
    assert client.request("DELETE", f"/api/auth/passkeys/{key_id}", headers=headers, json={"password": ACCOUNT["password"], "code": "123456"}).status_code == 200
    with client.app.state.database.sessions() as db:
        second = User(email="second@example.com", first_name="Second", password_hash="hash"); db.add(second); db.flush()
        key = Passkey(user_id=second.id, credential_id=b"other", public_key=b"pub", sign_count=0, created_at=1); db.add(key); db.commit(); other_id = key.id
    assert client.request("DELETE", f"/api/auth/passkeys/{other_id}", headers=headers, json={"password": ACCOUNT["password"], "code": "123456"}).status_code == 404
    svc = service(client); user = svc.session.get(User, 2); user.password_hash = None; svc.session.commit()
    with pytest.raises(HTTPException) as error: svc.delete(user, other_id)
    assert error.value.status_code == 409
