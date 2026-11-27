from types import SimpleNamespace

from sqlalchemy import select

from app.database.models.security_event import SecurityEvent
from app.database.models.user import User
from app.security.client_ip import resolve_client_ip
from app.security.rate_limiter import MemoryRateLimitStore, RateLimiter
from app.services.auth_service import AuthService
from app.services.risk_engine import RiskEngine
from app.services.security_event_service import SecurityEventService
from tests.test_auth import ACCOUNT
from tests.test_mfa import enable


def proxied_request(settings, direct='10.0.0.2', forwarded='198.51.100.8, 203.0.113.4', ua='Chrome'):
    return SimpleNamespace(
        client=SimpleNamespace(host=direct),
        headers={'x-forwarded-for': forwarded, 'user-agent': ua},
        app=SimpleNamespace(state=SimpleNamespace(settings=settings)),
    )


def test_totp_rejects_same_and_older_counter_but_accepts_newer(client, monkeypatch):
    enable(client)
    monkeypatch.setattr('app.services.auth_service.totp.verify', lambda _secret, value: int(value))
    with client.app.state.database.sessions() as db:
        auth = AuthService(db, client.app.state.settings)
        user = db.scalar(select(User))
        assert auth._verify_mfa_code(user, '100') is True
        db.commit()
        assert auth._verify_mfa_code(user, '100') is False
        assert auth._verify_mfa_code(user, '99') is False
        assert auth._verify_mfa_code(user, '101') is True
        db.commit()


def test_totp_counter_claim_is_compare_and_set(client, monkeypatch):
    enable(client)
    monkeypatch.setattr('app.services.auth_service.totp.verify', lambda _secret, value: int(value))
    database = client.app.state.database
    first, second = database.sessions(), database.sessions()
    try:
        first_auth = AuthService(first, client.app.state.settings)
        second_auth = AuthService(second, client.app.state.settings)
        assert first_auth._verify_mfa_code(first.scalar(select(User)), '200') is True
        first.commit()
        assert second_auth._verify_mfa_code(second.scalar(select(User)), '200') is False
    finally:
        first.close()
        second.close()


def test_copied_user_agent_cannot_claim_known_device(client):
    client.post('/api/auth/register', json=ACCOUNT)
    with client.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        SecurityEventService(db).record(user.id, 'login_success', request=proxied_request(client.app.state.settings, direct='1.2.3.4', forwarded='', ua='Copied UA'))
        db.commit()
        result = RiskEngine(db, client.app.state.settings).evaluate(
            user.id, request=proxied_request(client.app.state.settings, direct='5.6.7.8', forwarded='', ua='Copied UA')
        )
    assert 'known_device' not in result.signals and 'new_ip' in result.signals


def test_server_verified_session_ip_is_not_a_device_binding(client):
    client.post('/api/auth/register', json=ACCOUNT)
    with client.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        SecurityEventService(db).record(user.id, 'login_success', request=proxied_request(client.app.state.settings, direct='1.2.3.4', forwarded='', ua='Old UA'))
        db.commit()
        result = RiskEngine(db, client.app.state.settings).evaluate(
            user.id, request=proxied_request(client.app.state.settings, direct='1.2.3.4', forwarded='', ua='New UA')
        )
    assert 'known_device' not in result.signals and 'new_device' in result.signals


def test_trusted_proxy_ip_is_shared_by_limiter_risk_and_events(client):
    client.post('/api/auth/register', json=ACCOUNT)
    settings = client.app.state.settings
    settings.trusted_proxies = ['10.0.0.2', '203.0.113.4']
    request = proxied_request(settings)
    expected = '198.51.100.8'
    assert resolve_client_ip(request) == expected
    captured = []
    limiter = RateLimiter(settings, MemoryRateLimitStore())
    original_key = limiter._key
    limiter._key = lambda operation, part, value: (captured.append(value) if part == 'ip' else None) or original_key(operation, part, value)
    limiter.check('login', request)
    with client.app.state.database.sessions() as db:
        user = db.scalar(select(User))
        SecurityEventService(db).record(user.id, 'login_success', request=request)
        db.commit()
        event = db.scalar(select(SecurityEvent).where(SecurityEvent.user_id == user.id, SecurityEvent.event_type == 'login_success'))
        result = RiskEngine(db, settings).evaluate(user.id, request=request)
    assert captured == [expected] and event.ip == expected and 'known_device' not in result.signals
