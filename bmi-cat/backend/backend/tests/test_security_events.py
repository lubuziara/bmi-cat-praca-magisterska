import base64
from types import SimpleNamespace
from sqlalchemy import select
from app.database.models.security_event import SecurityEvent
from app.security.token_digest import token_digest
from tests.test_auth import ACCOUNT
from tests.test_mfa import enable, login_challenge, code
from tests.test_passkeys import credential

def event_rows(client):
    with client.app.state.database.sessions() as db:
        return db.scalars(select(SecurityEvent).order_by(SecurityEvent.id)).all()

def assert_no_secrets(rows, secrets):
    text = str([{'type': e.event_type, 'metadata': e.metadata_json, 'ip': e.ip, 'ua': e.user_agent} for e in rows])
    for secret in secrets:
        assert secret not in text

def test_login_events_are_private_and_paginated(client):
    client.post('/api/auth/register', json=ACCOUNT)
    bad = client.post('/api/auth/login', json={**ACCOUNT, 'password': 'wrong'})
    login = client.post('/api/auth/login', json=ACCOUNT).json()
    events = client.get('/api/auth/security-events?limit=1', headers={'Authorization': 'Bearer ' + login['access_token']})
    assert events.status_code == 200 and len(events.json()) == 1
    assert 'password' not in str(events.json()) and 'token' not in str(events.json())
    all_events = client.get('/api/auth/security-events?limit=100', headers={'Authorization': 'Bearer ' + login['access_token']}).json()
    assert {'login_success', 'login_failed'} <= {e['event_type'] for e in all_events}

def test_events_cannot_be_read_by_another_user(client):
    first = client.post('/api/auth/register', json=ACCOUNT).json()
    client.post('/api/auth/login', json=ACCOUNT)
    second = client.post('/api/auth/register', json={**ACCOUNT, 'email': 'other@example.com'}).json()
    events = client.get('/api/auth/security-events', headers={'Authorization': 'Bearer ' + second['access_token']}).json()
    assert all(e['event_type'] != 'login_success' for e in events)

def test_logout_and_session_revoke_events(client, monkeypatch):
    client.post('/api/auth/register', json=ACCOUNT)
    one = client.post('/api/auth/login', json=ACCOUNT).json(); two = client.post('/api/auth/login', json=ACCOUNT).json()
    headers = {'Authorization': 'Bearer ' + one['access_token']}
    target = next(s['id'] for s in client.get('/api/auth/sessions', headers=headers).json() if not s['is_current'])
    assert client.delete('/api/auth/sessions/' + target, headers=headers).status_code == 200
    assert client.post('/api/auth/logout', headers={'Authorization': 'Bearer ' + two['access_token']}).status_code == 200
    client.post('/api/auth/login', json=ACCOUNT)
    monkeypatch.setattr('app.services.auth_service.AuthService._require_reauthentication', lambda *args: None)
    assert client.post('/api/auth/sessions/revoke-others', headers=headers, json={'password': ACCOUNT['password'], 'code': '123456'}).status_code == 200
    events = client.get('/api/auth/security-events', headers=headers).json()
    assert any(e['event_type'] == 'session_revoked' for e in events)
    assert any(e['event_type'] == 'logout' for e in events)
    assert any(e['event_type'] == 'other_sessions_revoked' for e in events)

def test_password_reset_events_have_no_secrets(client):
    client.post('/api/auth/register', json=ACCOUNT)
    client.post('/api/auth/forgot-password', json={'email': ACCOUNT['email']})
    import re
    from email import message_from_string
    from pathlib import Path
    mail = next(Path(client.app.state.settings.outbox_dir).glob('*.eml')).read_text()
    body = message_from_string(mail).get_payload(decode=True).decode()
    token = re.search(r'token=([^\s]+)', body).group(1)
    assert client.post('/api/auth/reset-password', json={'token': token, 'password': 'Nowe poprawne hasło 123!'}).status_code == 200
    login = client.post('/api/auth/login', json={'email': ACCOUNT['email'], 'password': 'Nowe poprawne hasło 123!'}).json()
    events = client.get('/api/auth/security-events?limit=100', headers={'Authorization': 'Bearer ' + login['access_token']}).json()
    assert {'password_changed', 'password_reset_completed'} <= {e['event_type'] for e in events}
    assert 'Nowe poprawne hasło' not in str(events) and token not in str(events)

def test_security_event_limit_and_order(client):
    client.post('/api/auth/register', json=ACCOUNT)
    login = client.post('/api/auth/login', json=ACCOUNT).json()
    headers = {'Authorization': 'Bearer ' + login['access_token']}
    assert len(client.get('/api/auth/security-events?limit=1', headers=headers).json()) == 1
    assert client.get('/api/auth/security-events?limit=101', headers=headers).status_code == 422
    events = client.get('/api/auth/security-events?limit=100&user_id=999999', headers=headers).json()
    assert [e['created_at'] for e in events] == sorted((e['created_at'] for e in events), reverse=True)

def test_mfa_and_recovery_events_are_safe(client):
    secret, recovery, headers = enable(client)
    challenge = login_challenge(client)
    assert client.post('/api/auth/2fa/verify', json={'mfa_challenge': challenge, 'code': '000000'}).status_code == 401
    challenge2 = login_challenge(client)
    assert client.post('/api/auth/2fa/verify', json={'mfa_challenge': challenge2, 'code': recovery[0]}).status_code == 200
    regenerated = client.post('/api/auth/2fa/recovery/regenerate', headers=headers, json={'password': ACCOUNT['password'], 'code': code(secret)})
    assert regenerated.status_code == 200
    new_recovery = regenerated.json()['recovery_codes']
    assert client.post('/api/auth/2fa/disable', headers=headers, json={'password': ACCOUNT['password'], 'code': new_recovery[0]}).status_code == 200
    rows = event_rows(client); by_type = {e.event_type: e for e in rows}
    assert {'mfa_enabled', 'mfa_failed', 'recovery_code_used', 'recovery_codes_regenerated', 'mfa_disabled'} <= set(by_type)
    assert by_type['mfa_failed'].severity in {'warning', 'critical'}
    assert_no_secrets(rows, [secret, recovery[0], new_recovery[0], challenge, challenge2, '000000', token_digest(recovery[0])])

def test_passkey_events_are_safe(client, monkeypatch):
    client.app.state.settings.webauthn_rp_id = 'localhost'; client.app.state.settings.webauthn_origin = 'http://localhost:5173'
    created = client.post('/api/auth/register', json=ACCOUNT).json(); headers = {'Authorization': 'Bearer ' + created['access_token']}
    monkeypatch.setattr('app.services.passkey_service.verify_registration_response', lambda **kw: SimpleNamespace(credential_id=b'event-key', credential_public_key=b'public', sign_count=0))
    options = client.post('/api/auth/passkeys/register/options', headers=headers, json={'password': ACCOUNT['password']}).json(); challenge = base64.urlsafe_b64decode(options['challenge'] + '=='); registration = credential(challenge, b'event-key')
    added = client.post('/api/auth/passkeys/register/verify', headers=headers, json={'credential': registration}); assert added.status_code == 200
    monkeypatch.setattr('app.services.passkey_service.verify_authentication_response', lambda **kw: SimpleNamespace(new_sign_count=0))
    options = client.post('/api/auth/passkeys/login/options').json(); login_ch = base64.urlsafe_b64decode(options['challenge'] + '=='); assertion = credential(login_ch, b'event-key')
    assert client.post('/api/auth/passkeys/login/verify', json={'credential': assertion}).status_code == 200
    monkeypatch.setattr('app.services.auth_service.AuthService._require_reauthentication', lambda *args: None)
    assert client.request('DELETE', f"/api/auth/passkeys/{added.json()['id']}", headers=headers, json={'password': ACCOUNT['password'], 'code': '123456'}).status_code == 200
    rows = event_rows(client); assert {'passkey_added', 'passkey_removed', 'passkey_login_success'} <= {e.event_type for e in rows}
    assert_no_secrets(rows, ['event-key', registration['response']['clientDataJSON'], assertion['response']['clientDataJSON'], options['challenge']])

def test_refresh_reuse_is_critical_and_contains_no_token(client):
    created = client.post('/api/auth/register', json=ACCOUNT).json(); old = created['refresh_token']
    assert client.post('/api/auth/refresh', json={'refresh_token': old}).status_code == 200
    assert client.post('/api/auth/refresh', json={'refresh_token': old}).status_code == 401
    rows = event_rows(client); event = next(e for e in rows if e.event_type == 'refresh_token_reuse_detected')
    assert event.severity == 'critical'
    assert_no_secrets([event], [old, token_digest(old)])
