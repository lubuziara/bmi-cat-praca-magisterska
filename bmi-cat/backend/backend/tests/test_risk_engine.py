import time
from types import SimpleNamespace
from sqlalchemy import select, func
from app.database.models.access_token import AccessToken
from app.database.models.security_event import SecurityEvent
from app.services.risk_engine import RiskEngine
from tests.test_auth import ACCOUNT

def request(ip='127.0.0.1', ua='Chrome Windows', device_id=None):
    headers = {'user-agent': ua}
    if device_id: headers['x-bmi-device-id'] = device_id
    return SimpleNamespace(client=SimpleNamespace(host=ip), headers=headers)

def add_event(db, user_id, event_type, *, ip=None, ua=None, severity='info'):
    db.add(SecurityEvent(user_id=user_id, event_type=event_type, created_at=int(time.time()), success=not event_type.endswith('failed'), severity=severity, ip=ip, user_agent=ua, metadata_json={}))

def user_id(client):
    client.post('/api/auth/register', json=ACCOUNT)
    with client.app.state.database.sessions() as db: return db.scalar(select(SecurityEvent.user_id).limit(1)) or 1

def engine(client):
    db = client.app.state.database.sessions(); return db, RiskEngine(db, client.app.state.settings)

def test_known_ip_does_not_claim_known_device(client):
    uid = user_id(client); db, risk = engine(client); add_event(db, uid, 'login_success', ip='1.2.3.4', ua='Chrome Windows'); db.commit()
    result = risk.evaluate(uid, request=request('1.2.3.4'), auth_method='passkey')
    assert result.level == 'low' and 'known_device' not in result.signals and {'new_device', 'passkey'} <= set(result.signals)

def test_new_device_and_platform_raise_risk(client):
    uid = user_id(client); db, risk = engine(client); add_event(db, uid, 'login_success', ip='1.2.3.4', ua='Chrome Windows'); db.commit()
    result = risk.evaluate(uid, request=request('1.2.3.4', 'BMICat Android'))
    assert result.score > 0 and {'new_device', 'platform_changed'} <= set(result.signals) and 'known_device' not in result.signals

def test_same_ip_and_user_agent_do_not_lower_score(client):
    uid = user_id(client); db, risk = engine(client); add_event(db, uid, 'login_success', ip='1.2.3.4', ua='Chrome Windows'); db.commit()
    result = risk.evaluate(uid, request=request('1.2.3.4', 'Chrome Windows'))
    assert result.score == risk.WEIGHTS['new_device'] and 'known_device' not in result.signals

def test_client_device_id_cannot_claim_known_device(client):
    uid = user_id(client); db, risk = engine(client); add_event(db, uid, 'login_success', ip='1.2.3.4', ua='Chrome Windows'); db.commit()
    result = risk.evaluate(uid, request=request('1.2.3.4', 'Chrome Windows', device_id='other-users-device'))
    assert result.score == risk.WEIGHTS['new_device'] and 'known_device' not in result.signals

def test_new_ip_alone_is_not_critical(client):
    uid = user_id(client); db, risk = engine(client); add_event(db, uid, 'login_success', ip='1.2.3.4', ua='Chrome Windows'); db.commit()
    result = risk.evaluate(uid, request=request('5.6.7.8'))
    assert 'new_ip' in result.signals and result.level != 'critical'

def test_failed_logins_raise_score(client):
    uid = user_id(client); db, risk = engine(client)
    for _ in range(3): add_event(db, uid, 'login_failed')
    db.commit(); result = risk.evaluate(uid)
    assert result.score >= 30 and 'failed_login' in result.signals

def test_failed_mfa_raises_score(client):
    uid = user_id(client); db, risk = engine(client)
    for _ in range(2): add_event(db, uid, 'mfa_failed', severity='warning')
    db.commit(); assert risk.evaluate(uid).score >= 30

def test_mfa_and_passkey_reduce_risk(client):
    uid = user_id(client); db, risk = engine(client)
    for _ in range(3): add_event(db, uid, 'login_failed')
    db.commit(); plain = risk.evaluate(uid).score
    assert risk.evaluate(uid, auth_method='passkey', mfa_used=True).score < plain

def test_reuse_detection_is_critical(client):
    uid = user_id(client); db, risk = engine(client); add_event(db, uid, 'refresh_token_reuse_detected', severity='critical'); db.commit()
    result = risk.evaluate(uid); assert result.level == 'critical' and result.action == 'block'

def test_score_is_always_bounded(client):
    uid = user_id(client); db, risk = engine(client)
    for _ in range(4): add_event(db, uid, 'login_failed'); add_event(db, uid, 'mfa_failed'); add_event(db, uid, 'refresh_token_reuse_detected')
    db.commit(); assert 0 <= risk.evaluate(uid).score <= 100

def test_medium_requires_step_up_without_session_or_score(client):
    created = client.post('/api/auth/register', json=ACCOUNT).json()
    for _ in range(3): client.post('/api/auth/login', json={**ACCOUNT, 'password': 'wrong'})
    with client.app.state.database.sessions() as db: before = db.scalar(select(func.count()).select_from(AccessToken))
    response = client.post('/api/auth/login', json=ACCOUNT); body = response.json()
    with client.app.state.database.sessions() as db:
        after = db.scalar(select(func.count()).select_from(AccessToken)); types = set(db.scalars(select(SecurityEvent.event_type)))
    assert response.status_code == 200 and body['step_up_required'] is True and before == after
    assert 'risk_score' not in body and 'signals' not in body and {'risk_medium_detected', 'step_up_auth_required'} <= types

def test_high_does_not_issue_session(client):
    client.post('/api/auth/register', json=ACCOUNT)
    with client.app.state.database.sessions() as db:
        for _ in range(3): add_event(db, 1, 'login_failed')
        for _ in range(2): add_event(db, 1, 'mfa_failed', severity='warning')
        before = db.scalar(select(func.count()).select_from(AccessToken)); db.commit()
    response = client.post('/api/auth/login', json=ACCOUNT)
    with client.app.state.database.sessions() as db: after = db.scalar(select(func.count()).select_from(AccessToken)); types = set(db.scalars(select(SecurityEvent.event_type)))
    assert response.json()['step_up_required'] is True and before == after and 'risk_high_detected' in types

def test_critical_blocks_and_emits_event(client):
    client.post('/api/auth/register', json=ACCOUNT)
    with client.app.state.database.sessions() as db: add_event(db, 1, 'refresh_token_reuse_detected', severity='critical'); before = db.scalar(select(func.count()).select_from(AccessToken)); db.commit()
    response = client.post('/api/auth/login', json=ACCOUNT)
    with client.app.state.database.sessions() as db: after = db.scalar(select(func.count()).select_from(AccessToken)); event = db.scalar(select(SecurityEvent).where(SecurityEvent.event_type == 'risk_critical_detected'))
    assert response.status_code == 401 and before == after and event is not None
    assert 'risk_score' not in response.text and 'signals' not in response.text
