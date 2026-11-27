import json
import time
from urllib.parse import urlparse, parse_qs
from cryptography.fernet import Fernet
from sqlalchemy import select
from app.database.models.calendar_connection import CalendarConnection
from app.database.models.calendar_oauth_state import CalendarOAuthState
from app.services.calendar_provider import CalendarProvider
from app.services.calendar_oauth_service import CalendarOAuthService
from test_diary import verified


class ProviderResponse:
    def __init__(self, data, status=200):
        self.data, self.status_code = data, status

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError('test failure')

    def json(self):
        return self.data


def configure(client):
    settings = client.app.state.settings
    settings.calendar_token_key = Fernet.generate_key().decode()
    settings.google_calendar_client_id = 'test-google'
    settings.google_calendar_client_secret = 'test-secret'
    settings.outlook_client_id = 'test-outlook'
    settings.outlook_client_secret = 'test-secret'


def test_oauth_state_pkce_encryption_and_replay(client, monkeypatch):
    headers = verified(client)
    assert client.post('/api/auth/calendar-connections/google/connect', headers=headers).status_code == 503
    configure(client)
    monkeypatch.setattr('app.services.calendar_oauth_service.requests.post', lambda *a, **k: ProviderResponse({'access_token': 'test-access', 'refresh_token': 'test-refresh', 'expires_in': 3600}))
    monkeypatch.setattr('app.services.calendar_oauth_service.requests.get', lambda *a, **k: ProviderResponse({'sub': 'test-account', 'id': 'test-calendar'}))
    for provider in ['google', 'outlook']:
        result = client.post(f'/api/auth/calendar-connections/{provider}/connect', headers=headers)
        query = parse_qs(urlparse(result.json()['url']).query)
        assert query['code_challenge_method'] == ['S256']
        state = query['state'][0]
        callback = f'/api/auth/calendar-connections/{provider}/callback'
        assert client.get(callback, params={'state': 'tampered', 'code': 'test-code'}).status_code == 400
        assert client.get(callback, params={'state': state, 'code': 'test-code'}).status_code == 200
        assert client.get(callback, params={'state': state, 'code': 'test-code'}).status_code == 400
        with client.app.state.database.sessions() as db:
            connection = db.scalar(select(CalendarConnection).where(CalendarConnection.provider == provider))
            assert 'test-access' not in connection.tokens
            assert 'test-refresh' not in connection.tokens
            assert db.scalars(select(CalendarOAuthState)).all() == []
        assert client.post(f'/api/auth/calendar-connections/{provider}/disconnect', headers=headers).status_code == 200
    assert not any(c['connected'] for c in client.get('/api/auth/calendar-connections', headers=headers).json()['connections'])


def test_sync_create_update_delete_retry_and_refresh(client, monkeypatch):
    headers = verified(client)
    configure(client)
    user_id = client.get('/api/auth/me', headers=headers).json()['id']
    settings = client.app.state.settings
    token = {'access_token': 'expired', 'refresh_token': 'refresh-old', 'expires_at': 0}
    with client.app.state.database.sessions() as db:
        db.add(CalendarConnection(user_id=user_id, provider='google', tokens=Fernet(settings.calendar_token_key.encode()).encrypt(json.dumps(token).encode()).decode(), mappings={}))
        db.commit()
    monkeypatch.setattr('app.services.calendar_oauth_service.requests.post', lambda *a, **k: ProviderResponse({'access_token': 'renewed', 'refresh_token': 'rotated', 'expires_in': 3600}))
    calls, removed = [], []
    def upsert(self, event, cat_name, remote_id, identity):
        calls.append((event['title'], remote_id, identity))
        return remote_id or 'remote-' + identity
    monkeypatch.setattr(CalendarProvider, 'upsert', upsert)
    monkeypatch.setattr(CalendarProvider, 'remove', lambda self, key: removed.append(key))
    body = {'chest_cm': 40, 'leg_cm': 16, 'occurred_at': '2026-09-11T10:00:00+02:00'}
    first = client.post('/api/auth/bmi', headers=headers, json=body).json()
    worker = client.app.state.calendar_sync
    worker.sync(user_id, 'google'); worker.sync(user_id, 'google')
    assert len(calls) == 1
    client.post('/api/auth/bmi', headers=headers, json={**body, 'chest_cm': 39})
    worker.sync(user_id, 'google')
    assert len(calls) == 2 and calls[1][1] is not None
    client.post(f"/api/auth/calendar/{first['id']}/remove", headers=headers)
    worker.sync(user_id, 'google'); worker.sync(user_id, 'google')
    assert len(removed) == 1
    client.post('/api/auth/bmi', headers=headers, json=body)
    worker.sync(user_id, 'google')
    assert calls[-1][2] != calls[0][2]
    with client.app.state.database.sessions() as db:
        conn = db.get(CalendarConnection, (user_id, 'google'))
        token = json.loads(Fernet(settings.calendar_token_key.encode()).decrypt(conn.tokens.encode()))
        assert token['refresh_token'] == 'rotated'
        assert conn.error is None and conn.last_sync
    client.post('/api/auth/bmi', headers=headers, json={**body, 'chest_cm': 38})
    monkeypatch.setattr(CalendarProvider, 'upsert', lambda *a: (_ for _ in ()).throw(RuntimeError('offline')))
    worker.sync(user_id, 'google')
    with client.app.state.database.sessions() as db:
        assert db.get(CalendarConnection, (user_id, 'google')).error
    monkeypatch.setattr(CalendarProvider, 'upsert', upsert)
    worker.sync(user_id, 'google')
    with client.app.state.database.sessions() as db:
        assert db.get(CalendarConnection, (user_id, 'google')).error is None


def test_provider_payload_dates_and_privacy():
    event = {'title': 'Dokument', 'day': '2026-09-11', 'occurred_at': '2026-09-11T00:15:00+02:00', 'details': {'note': 'private'}}
    google = CalendarProvider('google', 'test').payload(event, 'Luna')
    outlook = CalendarProvider('outlook', 'test').payload(event, 'Luna')
    assert google['start']['dateTime'] == '2026-09-10T22:15:00+00:00'
    assert outlook['start']['timeZone'] == 'UTC'
    assert 'private' not in json.dumps([google, outlook])
    day = CalendarProvider('google', 'test').payload({**event, 'occurred_at': None}, 'Luna')
    assert day['start'] == {'date': '2026-09-11'}
    assert day['end'] == {'date': '2026-09-12'}
