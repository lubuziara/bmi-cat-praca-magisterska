import base64
import time
from types import SimpleNamespace

from sqlalchemy import func, select

from app.database.models.access_token import AccessToken
from app.database.models.passkey import Passkey
from app.database.models.step_up_challenge import StepUpChallenge
from app.database.models.security_event import SecurityEvent
from app.database.models.user import User
from app.security.token_digest import token_digest
from tests.test_auth import ACCOUNT
from tests.test_mfa import code, enable
from tests.test_passkeys import credential


def risky_login(client, register=True):
    if register: client.post('/api/auth/register', json=ACCOUNT)
    for _ in range(3): client.post('/api/auth/login', json={**ACCOUNT, 'password': 'wrong'})
    return client.post('/api/auth/login', json=ACCOUNT)


def test_risk_step_up_is_hashed_short_lived_and_has_no_session(client):
    client.post('/api/auth/register', json=ACCOUNT)
    with client.app.state.database.sessions() as db: before = db.scalar(select(func.count()).select_from(AccessToken))
    response = risky_login(client, register=False); body = response.json()
    with client.app.state.database.sessions() as db:
        row = db.get(StepUpChallenge, token_digest(body['step_up_challenge']))
        after = db.scalar(select(func.count()).select_from(AccessToken))
    assert response.status_code == 200 and after == before
    assert row and row.expires_at - int(time.time()) <= 300 and row.digest != body['step_up_challenge']
    assert set(body) == {'step_up_required', 'step_up_challenge', 'methods', 'expires_in'}


def test_expired_or_disallowed_step_up_cannot_create_session(client):
    body = risky_login(client).json(); raw = body['step_up_challenge']
    with client.app.state.database.sessions() as db:
        db.get(StepUpChallenge, token_digest(raw)).expires_at = int(time.time()) - 1; db.commit()
    assert client.post('/api/auth/step-up/passkey/options', json={'step_up_challenge': raw}).status_code == 401
    assert client.post('/api/auth/step-up/verify', json={'step_up_challenge': raw, 'code': '000000'}).status_code == 401


def test_passkey_step_up_completes_once_and_is_bound_to_user(client, monkeypatch):
    client.app.state.settings.webauthn_rp_id = 'localhost'; client.app.state.settings.webauthn_origin = 'http://localhost:5173'
    body = risky_login(client).json(); raw = body['step_up_challenge']
    with client.app.state.database.sessions() as db:
        db.add(Passkey(user_id=1, credential_id=b'owner-key', public_key=b'pub', sign_count=0, created_at=1)); db.commit()
    monkeypatch.setattr('app.services.passkey_service.verify_authentication_response', lambda **kw: SimpleNamespace(new_sign_count=1))
    options = client.post('/api/auth/step-up/passkey/options', json={'step_up_challenge': raw}).json()
    assertion = credential(base64.urlsafe_b64decode(options['challenge'] + '=='), b'owner-key')
    success = client.post('/api/auth/step-up/passkey/verify', json={'step_up_challenge': raw, 'credential': assertion})
    assert success.status_code == 200 and 'access_token' in success.json()
    assert client.post('/api/auth/step-up/passkey/verify', json={'step_up_challenge': raw, 'credential': assertion}).status_code == 401
    with client.app.state.database.sessions() as db:
        assert db.get(StepUpChallenge, token_digest(raw)).used_at is not None
        assert 'step_up_auth_success' in set(db.scalars(select(SecurityEvent.event_type)))


def test_bad_passkey_step_up_creates_no_session_and_records_failure(client, monkeypatch):
    client.app.state.settings.webauthn_rp_id = 'localhost'; client.app.state.settings.webauthn_origin = 'http://localhost:5173'
    body = risky_login(client).json(); raw = body['step_up_challenge']
    with client.app.state.database.sessions() as db: db.add(Passkey(user_id=1, credential_id=b'key', public_key=b'pub', sign_count=0, created_at=1)); db.commit()
    monkeypatch.setattr('app.services.passkey_service.verify_authentication_response', lambda **kw: (_ for _ in ()).throw(ValueError('bad')))
    with client.app.state.database.sessions() as db: before = db.scalar(select(func.count()).select_from(AccessToken))
    assert client.post('/api/auth/step-up/passkey/verify', json={'step_up_challenge': raw, 'credential': credential(base64.urlsafe_b64decode(raw + '=='), b'key')}).status_code == 401
    with client.app.state.database.sessions() as db:
        assert db.scalar(select(func.count()).select_from(AccessToken)) == before
        assert 'step_up_auth_failed' in set(db.scalars(select(SecurityEvent.event_type)))


def test_step_up_for_user_a_rejects_user_b_passkey(client, monkeypatch):
    client.app.state.settings.webauthn_rp_id = 'localhost'; client.app.state.settings.webauthn_origin = 'http://localhost:5173'
    raw = risky_login(client).json()['step_up_challenge']
    with client.app.state.database.sessions() as db:
        other = User(email='other@example.com', first_name='Other', password_hash='hash'); db.add(other); db.flush()
        db.add(Passkey(user_id=other.id, credential_id=b'other-key', public_key=b'pub', sign_count=0, created_at=1)); db.commit()
    monkeypatch.setattr('app.services.passkey_service.verify_authentication_response', lambda **kw: SimpleNamespace(new_sign_count=1))
    assertion = credential(base64.urlsafe_b64decode(raw + '=='), b'other-key')
    assert client.post('/api/auth/step-up/passkey/verify', json={'step_up_challenge': raw, 'credential': assertion}).status_code == 401


def test_totp_step_up_works_only_when_explicitly_allowed(client):
    secret, _, _ = enable(client)
    for _ in range(3): client.post('/api/auth/login', json={**ACCOUNT, 'password': 'wrong'})
    body = client.post('/api/auth/login', json=ACCOUNT).json()
    assert {'passkey', 'totp', 'recovery_code'} == set(body['methods'])
    result = client.post('/api/auth/step-up/verify', json={'step_up_challenge': body['step_up_challenge'], 'code': code(secret)})
    assert result.status_code == 200 and 'access_token' in result.json()
