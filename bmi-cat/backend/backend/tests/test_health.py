import base64
import io
import pytest
from PIL import Image
from pypdf import PdfReader
from test_diary import verified

STAMP = '2026-09-11T00:15:00+02:00'


def image_payload():
    stream = io.BytesIO()
    Image.new('RGB', (640, 900), 'white').save(stream, 'PNG')
    return {'title': 'Wizyta kontrolna', 'occurred_at': STAMP,
            'image_base64': base64.b64encode(stream.getvalue()).decode()}


def test_documents_calendar_pdf_and_ownership(client):
    headers = verified(client)
    other = verified(client, 'other-health@example.com')
    response = client.post('/api/auth/documents', headers=headers, json=image_payload())
    assert response.status_code == 201, response.text
    document_id = response.json()['id']
    path = f'/api/auth/documents/{document_id}'
    assert client.get(path, headers=other).status_code == 404
    assert client.get(path + '/pdf', headers=other).status_code == 404
    assert client.post(path + '/remove', headers=other).status_code == 404
    pdf = client.get(path + '/pdf', headers=headers)
    assert pdf.headers['content-type'] == 'application/pdf'
    assert pdf.headers['cache-control'] == 'no-store'
    reader = PdfReader(io.BytesIO(pdf.content))
    assert len(reader.pages) == 1
    preview = client.get(path, headers=headers).json()
    assert Image.open(io.BytesIO(base64.b64decode(preview['image_base64']))).size == (640, 900)
    events = client.get('/api/auth/calendar?start=2026-09-11&end=2026-09-11', headers=headers).json()['events']
    assert len(events) == 1
    assert events[0]['occurred_at'] == STAMP
    assert events[0]['details']['document_id'] == document_id
    assert client.post(path + '/remove', headers=headers).status_code == 200
    assert client.get(path, headers=headers).status_code == 404
    assert client.get('/api/auth/calendar?start=2026-09-11&end=2026-09-11', headers=headers).json()['events'] == []


def test_bmi_replaces_daily_measurement_and_meals_aggregate(client):
    headers = verified(client)
    body = {'chest_cm': 40, 'leg_cm': 16, 'occurred_at': STAMP}
    first = client.post('/api/auth/bmi', json=body, headers=headers)
    assert first.status_code == 200, first.text
    second = client.post('/api/auth/bmi', json={**body, 'chest_cm': 39, 'occurred_at': '2026-09-11T19:15:00+02:00'}, headers=headers)
    assert first.json()['id'] == second.json()['id']
    assert second.json()['details']['value'] == round(((39/.7062-16)/.9156)-16, 2)
    for grams in [50, 100]:
        client.post('/api/auth/diary', headers=headers, json={'day': '2026-09-11', 'period': 'morning', 'food_id': 'demo-chicken-can', 'grams': grams})
    events = client.get('/api/auth/calendar?start=2026-09-11&end=2026-09-11', headers=headers).json()['events']
    assert len(events) == 2
    assert next(e for e in events if e['kind'] == 'nutrition')['details']['kcal'] == 150


def test_vet_medication_settings_and_invalid_data(client):
    headers = verified(client)
    for kind in ['vet', 'medication']:
        result = client.post('/api/auth/calendar', headers=headers, json={'kind': kind, 'title': 'Kontrola', 'occurred_at': STAMP})
        assert result.status_code == 201
    prefs = client.get('/api/auth/settings', headers=headers).json()
    prefs.pop('email'); prefs.pop('phone')
    assert client.post('/api/auth/settings', headers=headers, json={**prefs, 'first_name': '666'}).status_code == 422
    assert client.post('/api/auth/settings', headers=headers, json={**prefs, 'target_kcal': -100}).status_code == 422
    assert client.post('/api/auth/settings', headers=headers, json={**prefs, 'target_kcal': 240, 'cat_name': 'Luna', 'notifications': False}).status_code == 200
    assert client.get('/api/auth/diary?day=2026-09-11', headers=headers).json()['target_kcal'] == 240
    assert client.get('/api/auth/profile', headers=headers).json()['cat']['name'] == 'Luna'
    for body in [dict(chest_cm=0, leg_cm=16), dict(chest_cm='NaN', leg_cm=16), dict(chest_cm=40, leg_cm=0), dict(chest_cm=1, leg_cm=50)]:
        assert client.post('/api/auth/bmi', headers=headers, json={**body, 'occurred_at': STAMP}).status_code == 422
    for bad in ['<html>not an image</html>', 'not_base64']:
        assert client.post('/api/auth/documents', headers=headers, json={**image_payload(), 'image_base64': bad}).status_code == 422


@pytest.mark.parametrize('path', ['/calendar?start=2026-09-11&end=2026-09-11', '/documents', '/settings', '/calendar-connections'])
def test_health_requires_login(client, path):
    assert client.get('/api/auth' + path).status_code == 401
