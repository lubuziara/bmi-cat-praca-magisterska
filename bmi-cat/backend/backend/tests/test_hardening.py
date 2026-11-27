from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.mailer import Mailer
from tests.test_auth import ACCOUNT


def test_security_headers_and_clickjacking(client):
    headers = client.get('/api/auth/health').headers
    assert headers['x-content-type-options'] == 'nosniff'
    assert headers['referrer-policy'] == 'strict-origin-when-cross-origin'
    assert headers['x-frame-options'] == 'DENY'
    assert "frame-ancestors 'none'" in headers['content-security-policy']
    assert headers['cross-origin-opener-policy'] == 'same-origin-allow-popups'
    assert headers['cache-control'] == 'no-store'


def test_hsts_only_in_production(tmp_path):
    dev = TestClient(create_app(Settings(database_url=f'sqlite:///{tmp_path / "dev.db"}', cookie_secure=False, _env_file=None)))
    prod_settings = Settings(environment='production', database_url=f'sqlite:///{tmp_path / "prod.db"}', frontend_url='https://app.example', api_base_url='https://api.example', android_api_base_url='https://api.example', cors_origins=['https://app.example'], mail_mode='smtp', sms_provider='not_configured', _env_file=None)
    prod = TestClient(create_app(prod_settings), base_url='https://api.example')
    assert 'strict-transport-security' not in dev.get('/api/auth/health').headers
    assert prod.get('/api/auth/health').headers['strict-transport-security'] == 'max-age=31536000'


def test_cors_is_explicit_and_rejects_unknown_origin(client):
    allowed = client.options('/api/auth/login', headers={'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST'})
    rejected = client.options('/api/auth/login', headers={'Origin': 'https://evil.example', 'Access-Control-Request-Method': 'POST'})
    assert allowed.headers['access-control-allow-origin'] == 'http://localhost:5173'
    assert 'access-control-allow-origin' not in rejected.headers
    with pytest.raises(ValueError): Settings(cors_origins=['*'], _env_file=None)


def test_forgot_reset_and_verification_do_not_expose_secrets(client):
    known = client.post('/api/auth/forgot-password', json={'email': ACCOUNT['email']})
    unknown = client.post('/api/auth/forgot-password', json={'email': 'unknown@example.com'})
    assert known.status_code == unknown.status_code == 200 and known.json() == unknown.json()
    assert 'token' not in known.text and 'code' not in known.text
    assert client.post('/api/auth/reset-password', json={'token': 'x' * 32, 'password': 'Nowe bezpieczne hasło 123!'}).status_code == 400
    assert client.post('/api/auth/verification/send', json={'channel': 'email'}).status_code == 401


def test_cookie_state_changes_require_csrf(client):
    client.post('/api/auth/register', json=ACCOUNT)
    web = {'X-BMI-Client': 'web'}
    client.post('/api/auth/login', json=ACCOUNT, headers=web)
    assert client.post('/api/auth/refresh', headers=web).status_code == 403
    assert client.post('/api/auth/logout', headers=web).status_code == 403


def test_production_error_is_generic_and_local_mail_is_blocked(tmp_path):
    settings = Settings(environment='production', database_url=f'sqlite:///{tmp_path / "error.db"}', frontend_url='https://app.example', api_base_url='https://api.example', android_api_base_url='https://api.example', cors_origins=['https://app.example'], mail_mode='smtp', sms_provider='not_configured', _env_file=None)
    app = create_app(settings)
    @app.get('/boom')
    def boom(): raise RuntimeError('SQL secret detail')
    response = TestClient(app, base_url='https://api.example', raise_server_exceptions=False).get('/boom')
    assert response.status_code == 500 and 'SQL secret detail' not in response.text and 'traceback' not in response.text.lower()
    settings.mail_mode = 'local'
    with pytest.raises(ValueError): Mailer(settings).send_reset('cat@example.com', 'secret')
    assert not list(Path(tmp_path).glob('*.eml'))
