import sys
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.config import Settings
from app.security.rate_limiter import MemoryRateLimitStore, create_rate_limiter
from app.services.sms_sender import SmsSender


def production_settings(**changes):
    values = {
        'environment': 'production', 'cookie_secure': True, 'mail_mode': 'smtp',
        'frontend_url': 'https://app.example.test', 'api_base_url': 'https://api.example.test',
        'android_api_base_url': 'https://api.example.test', 'cors_origins': ['https://app.example.test'],
        'sms_provider': 'not_configured', '_env_file': None,
    }
    values.update(changes)
    return Settings(**values)


def test_development_uses_memory_and_file_sms(tmp_path):
    settings = Settings(cookie_secure=False, sms_outbox_dir=str(tmp_path), _env_file=None)
    assert isinstance(create_rate_limiter(settings).store, MemoryRateLimitStore)
    SmsSender(settings).send('+48123456789', '123456')
    assert len(list(tmp_path.glob('*.txt'))) == 1


def test_redis_requires_valid_url_and_accepts_tls_url():
    with pytest.raises(ValueError, match='BMI_REDIS_URL'):
        Settings(rate_limit_backend='redis', cookie_secure=False, _env_file=None)
    settings = Settings(rate_limit_backend='redis', redis_url='rediss://cache.example.test:6380/0', cookie_secure=False, _env_file=None)
    assert settings.redis_url.startswith('rediss://')


def test_multi_instance_production_cannot_use_memory():
    with pytest.raises(ValueError, match='Multi-instance'):
        production_settings(rate_limit_instances=2)


def test_redis_startup_failure_is_safe_and_never_falls_back(monkeypatch):
    secret_url = 'redis://:private-password@cache.example.test:6379/0'

    class FailingClient:
        def ping(self): raise RuntimeError(secret_url)

    monkeypatch.setitem(sys.modules, 'redis', SimpleNamespace(from_url=lambda *_args, **_kwargs: FailingClient()))
    with pytest.raises(RuntimeError) as error:
        create_rate_limiter(production_settings(rate_limit_backend='redis', redis_url=secret_url))
    assert 'private-password' not in str(error.value)


def test_production_rejects_file_sms_provider(tmp_path):
    with pytest.raises(ValueError, match='file provider'):
        production_settings(sms_provider='file', sms_outbox_dir=str(tmp_path))
    assert not list(tmp_path.glob('*'))


def test_unconfigured_production_sms_refuses_without_code_or_file(tmp_path):
    settings = production_settings(sms_outbox_dir=str(tmp_path))
    with pytest.raises(HTTPException) as error:
        SmsSender(settings).send('+48123456789', '123456')
    assert error.value.status_code == 503 and '123456' not in str(error.value.detail)
    assert not list(tmp_path.glob('*'))
