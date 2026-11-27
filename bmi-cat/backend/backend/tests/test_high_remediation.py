import base64
import re
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.database.models.passkey import PasskeyChallenge
from app.database.models.user import User
from app.database.models.user_mfa import MfaSetup
from app.main import create_app
from app.security.token_digest import token_digest
from tests.test_auth import ACCOUNT
from tests.test_mfa import code
from tests.test_passkeys import credential


def register(client, account=ACCOUNT):
    result = client.post('/api/auth/register', json=account)
    assert result.status_code == 201
    return {'Authorization': 'Bearer ' + result.json()['access_token']}


def test_passkey_registration_requires_reauth_and_challenge_is_bound_expiring_and_single_use(client, monkeypatch):
    client.app.state.settings.rate_limits['passkey']['limit'] = 50
    client.app.state.settings.webauthn_rp_id = 'localhost'
    client.app.state.settings.webauthn_origin = 'http://localhost:5173'
    owner = register(client)
    assert client.post('/api/auth/passkeys/register/options', headers=owner, json={}).status_code == 401
    options = client.post('/api/auth/passkeys/register/options', headers=owner,
                          json={'password': ACCOUNT['password']}).json()
    raw = base64.urlsafe_b64decode(options['challenge'] + '==')
    assertion = credential(raw, b'reauth-key')

    other_account = {**ACCOUNT, 'email': 'other@example.com', 'first_name': 'Ewa'}
    other = register(client, other_account)
    assert client.post('/api/auth/passkeys/register/verify', headers=other,
                       json={'credential': assertion}).status_code == 401

    monkeypatch.setattr('app.services.passkey_service.verify_registration_response',
                        lambda **kw: SimpleNamespace(credential_id=b'reauth-key', credential_public_key=b'public', sign_count=0))
    assert client.post('/api/auth/passkeys/register/verify', headers=owner,
                       json={'credential': assertion}).status_code == 200
    assert client.post('/api/auth/passkeys/register/verify', headers=owner,
                       json={'credential': assertion}).status_code == 401

    expiring = client.post('/api/auth/passkeys/register/options', headers=owner,
                           json={'password': ACCOUNT['password']}).json()['challenge']
    with client.app.state.database.sessions() as db:
        db.get(PasskeyChallenge, token_digest(expiring)).expires_at = int(time.time()) - 1
        db.commit()
    expired_assertion = credential(base64.urlsafe_b64decode(expiring + '=='), b'expired-key')
    assert client.post('/api/auth/passkeys/register/verify', headers=owner,
                       json={'credential': expired_assertion}).status_code == 401


def test_totp_setup_replacement_and_recovery_regeneration_require_reauth(client):
    bearer = register(client)
    assert client.post('/api/auth/2fa/setup', headers=bearer, json={}).status_code == 401
    setup = client.post('/api/auth/2fa/setup', headers=bearer,
                        json={'password': ACCOUNT['password']}).json()
    secret = re.search(r'secret=([^&]+)', setup['otpauth_uri']).group(1)
    confirmed = client.post('/api/auth/2fa/confirm', headers=bearer,
                            json={'setup_challenge': setup['setup_challenge'], 'code': code(secret)})
    recovery = confirmed.json()['recovery_codes']
    assert confirmed.status_code == 200

    assert client.post('/api/auth/2fa/setup', headers=bearer,
                       json={'password': ACCOUNT['password']}).status_code == 401
    replacement = client.post('/api/auth/2fa/setup', headers=bearer,
                              json={'password': ACCOUNT['password'], 'code': code(secret)})
    assert replacement.status_code == 200
    assert client.post('/api/auth/2fa/recovery/regenerate', headers=bearer,
                       json={'password': ACCOUNT['password']}).status_code == 401
    regenerated = client.post('/api/auth/2fa/recovery/regenerate', headers=bearer,
                              json={'password': ACCOUNT['password'], 'code': recovery[0]})
    assert regenerated.status_code == 200 and regenerated.json()['recovery_codes']


def test_totp_setup_challenge_is_user_bound_and_expires(client):
    owner = register(client)
    setup = client.post('/api/auth/2fa/setup', headers=owner,
                        json={'password': ACCOUNT['password']}).json()
    secret = re.search(r'secret=([^&]+)', setup['otpauth_uri']).group(1)
    other_account = {**ACCOUNT, 'email': 'other2@example.com', 'first_name': 'Ola'}
    other = register(client, other_account)
    assert client.post('/api/auth/2fa/confirm', headers=other,
                       json={'setup_challenge': setup['setup_challenge'], 'code': code(secret)}).status_code == 401
    with client.app.state.database.sessions() as db:
        db.get(MfaSetup, token_digest(setup['setup_challenge'])).expires_at = int(time.time()) - 1
        db.commit()
    assert client.post('/api/auth/2fa/confirm', headers=owner,
                       json={'setup_challenge': setup['setup_challenge'], 'code': code(secret)}).status_code == 401


def test_google_reauthentication_is_required_and_bound_to_google_subject(client, monkeypatch):
    bearer = register(client)
    with client.app.state.database.sessions() as db:
        user = db.get(User, 1)
        user.password_hash = None
        user.google_subject = 'google-owner'
        db.commit()
    client.app.state.settings.google_client_id = 'client'
    monkeypatch.setattr('app.services.google_auth_service.id_token.verify_oauth2_token',
                        lambda token, *args: {'sub': token, 'email_verified': True, 'iat': int(time.time())})
    stale = int(time.time()) - client.app.state.settings.reauth_seconds - 1
    monkeypatch.setattr('app.services.google_auth_service.id_token.verify_oauth2_token',
                        lambda token, *args: {'sub': token, 'email_verified': True, 'iat': stale})
    assert client.post('/api/auth/2fa/setup', headers=bearer,
                       json={'google_id_token': 'google-owner'}).status_code == 401
    monkeypatch.setattr('app.services.google_auth_service.id_token.verify_oauth2_token',
                        lambda token, *args: {'sub': token, 'email_verified': True, 'iat': int(time.time())})
    assert client.post('/api/auth/2fa/setup', headers=bearer,
                       json={'google_id_token': 'other'}).status_code == 401
    assert client.post('/api/auth/2fa/setup', headers=bearer,
                       json={'google_id_token': 'google-owner'}).status_code == 200


def production_settings(tmp_path, **overrides):
    values = dict(environment='production', database_url=f'sqlite:///{tmp_path / "prod.db"}',
                  frontend_url='https://app.example', api_base_url='https://api.example',
                  android_api_base_url='https://api.example', cors_origins=['https://app.example'],
                  mail_mode='smtp', sms_provider='not_configured', password_breach_check_enabled=False, _env_file=None)
    values.update(overrides)
    return Settings(**values)


def test_production_rejects_http_and_untrusted_forwarded_proto_but_trusted_proxy_works(tmp_path):
    settings = production_settings(tmp_path)
    app = create_app(settings)
    client = TestClient(app)
    assert client.get('/api/auth/me').status_code == 400
    assert client.get('/api/auth/me', headers={'X-Forwarded-Proto': 'https'}).status_code == 400

    settings.trusted_proxies = ['testclient']
    trusted = TestClient(create_app(settings))
    response = trusted.get('/api/auth/me', headers={'X-Forwarded-Proto': 'https'})
    assert response.status_code == 401
    assert response.headers['strict-transport-security'] == 'max-age=31536000'

    dev = TestClient(create_app(Settings(database_url=f'sqlite:///{tmp_path / "dev.db"}', cookie_secure=False, _env_file=None)))
    dev_response = dev.get('/api/auth/me')
    assert dev_response.status_code == 401 and 'strict-transport-security' not in dev_response.headers


def test_production_fails_fast_for_http_urls_and_keeps_secure_cookies(tmp_path):
    with pytest.raises(ValueError, match='HTTPS'):
        production_settings(tmp_path, api_base_url='http://api.example')
    with pytest.raises(ValueError):
        production_settings(tmp_path, webauthn_origin='http://app.example', webauthn_rp_id='app.example')

    settings = production_settings(tmp_path, trusted_proxies=['testclient'])
    client = TestClient(create_app(settings))
    headers = {'X-Forwarded-Proto': 'https', 'X-BMI-Client': 'web'}
    response = client.post('/api/auth/register', headers=headers, json=ACCOUNT)
    assert response.status_code == 201
    cookies = response.headers.get_list('set-cookie')
    assert cookies and all('Secure' in value for value in cookies)
    assert response.headers['strict-transport-security'] == 'max-age=31536000'
