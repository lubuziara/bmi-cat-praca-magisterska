from app.database.models.user_session import UserSession
from tests.test_auth import ACCOUNT

def login(client, email=ACCOUNT['email']):
    data = client.post('/api/auth/login', json={'email': email, 'password': ACCOUNT['password']}).json()
    return data, {'Authorization': 'Bearer ' + data['access_token']}

def test_sessions_are_independent_and_private(client):
    client.post('/api/auth/register', json=ACCOUNT)
    first, h1 = login(client); second, h2 = login(client)
    listed = client.get('/api/auth/sessions', headers=h1).json()
    assert len(listed) == 3 and sum(s['is_current'] for s in listed) == 1
    current = next(s for s in listed if s['is_current'])
    assert client.delete('/api/auth/sessions/' + current['id'], headers=h2).status_code == 200
    assert client.get('/api/auth/me', headers=h1).status_code == 401
    assert client.get('/api/auth/me', headers=h2).status_code == 200

def test_sessions_idor_and_revoke_others_require_reauth(client):
    client.post('/api/auth/register', json=ACCOUNT); one, h1 = login(client)
    other = dict(ACCOUNT, email='other@example.com'); client.post('/api/auth/register', json=other)
    theirs, h2 = login(client, other['email'])
    assert client.delete('/api/auth/sessions/' + theirs['access_token'], headers=h1).status_code == 404
    assert client.post('/api/auth/sessions/revoke-others', headers=h1, json={'password': 'bad', 'code': '123456'}).status_code == 401
