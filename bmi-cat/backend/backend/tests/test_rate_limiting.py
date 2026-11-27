from types import SimpleNamespace
from time import monotonic

import pytest
from fastapi import HTTPException

from app.config import Settings
from app.security.rate_limiter import MemoryRateLimitStore, RateLimiter, client_ip, create_rate_limiter


def request(ip, forwarded=None):
    headers = {} if forwarded is None else {'x-forwarded-for': forwarded}
    return SimpleNamespace(client=SimpleNamespace(host=ip), headers=headers)


def limiter():
    settings = Settings(cookie_secure=False, _env_file=None)
    settings.rate_limits['login'] = {'limit': 2, 'window': 60, 'failure_threshold': 2, 'failure_window': 60, 'cooldowns': [5, 10]}
    settings.rate_limits['mfa'] = {'limit': 1, 'window': 60, 'failure_threshold': 2, 'failure_window': 60, 'cooldowns': [5]}
    return RateLimiter(settings, MemoryRateLimitStore())


def test_login_is_limited_by_account_across_ips_and_by_ip_across_accounts():
    rate = limiter(); rate.check('login', request('1.1.1.1'), 'cat@example.com'); rate.check('login', request('2.2.2.2'), 'cat@example.com')
    with pytest.raises(HTTPException) as blocked: rate.check('login', request('3.3.3.3'), 'cat@example.com')
    assert blocked.value.status_code == 429 and blocked.value.headers['Retry-After']
    rate = limiter(); rate.check('login', request('1.1.1.1'), 'one@example.com'); rate.check('login', request('1.1.1.1'), 'two@example.com')
    with pytest.raises(HTTPException): rate.check('login', request('1.1.1.1'), 'three@example.com')


def test_mfa_has_separate_limit_and_neutral_response():
    rate = limiter(); rate.check('mfa', request('1.1.1.1'), 'challenge-a')
    with pytest.raises(HTTPException) as blocked: rate.check('mfa', request('1.1.1.1'), 'challenge-a')
    assert blocked.value.detail == 'Za dużo prób. Spróbuj ponownie później.'


def test_failure_cooldown_escalates_success_clears_and_expiry_allows_retry():
    rate = limiter(); rate.failure('login', 'cat@example.com'); rate.failure('login', 'cat@example.com')
    with pytest.raises(HTTPException): rate.check('login', request('9.9.9.9'), 'cat@example.com')
    rate.success('login', 'cat@example.com'); rate.check('login', request('9.9.9.9'), 'cat@example.com')
    key = 'cooldown:' + rate._key('login', 'subject', 'cat@example.com'); rate.store.set(key, 5, 1); rate.store.values[key] = (5, monotonic() - 1)
    rate.check('login', request('8.8.8.8'), 'cat@example.com')


def test_memory_store_and_proxy_trust_rules():
    rate = limiter(); assert isinstance(rate.store, MemoryRateLimitStore)
    assert client_ip(request('10.0.0.2', '203.0.113.4'), rate.settings) == '10.0.0.2'
    rate.settings.trusted_proxies = ['10.0.0.2']
    assert client_ip(request('10.0.0.2', '203.0.113.4'), rate.settings) == '203.0.113.4'


def test_redis_backend_is_selected_only_when_configured(monkeypatch):
    settings = Settings(rate_limit_backend='redis', redis_url='redis://example', cookie_secure=False, _env_file=None)
    monkeypatch.setattr('app.security.rate_limiter.RedisRateLimitStore', lambda url: MemoryRateLimitStore())
    assert isinstance(create_rate_limiter(settings).store, MemoryRateLimitStore)
