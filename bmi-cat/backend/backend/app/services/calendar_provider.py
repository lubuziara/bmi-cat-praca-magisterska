from datetime import datetime, timedelta, timezone, date
from urllib.parse import quote
import hashlib
import requests


class CalendarProvider:
    def __init__(self, provider, token):
        self.provider = provider
        self.headers = {'Authorization': f'Bearer {token}'}
        self.base = ('https://www.googleapis.com/calendar/v3/calendars/primary/events'
                     if provider == 'google' else 'https://graph.microsoft.com/v1.0/me/events')

    def payload(self, event, cat_name):
        title = f"BMI Cat • {cat_name}: {event['title']}"
        # Medical notes, images and attachments remain in BMI Cat.
        if event['occurred_at']:
            start = datetime.fromisoformat(event['occurred_at']).astimezone(timezone.utc)
            end = start + timedelta(minutes=30)
            google_times = {'start': {'dateTime': start.isoformat()}, 'end': {'dateTime': end.isoformat()}}
        else:
            day = date.fromisoformat(event['day'])
            start = datetime.combine(day, datetime.min.time(), timezone.utc)
            end = start + timedelta(days=1)
            google_times = {'start': {'date': day.isoformat()}, 'end': {'date': end.date().isoformat()}}
        if self.provider == 'google':
            return {'summary': title, 'description': 'Wydarzenie z BMI Cat. Szczegóły w aplikacji.', **google_times}
        return {'subject': title, 'body': {'contentType': 'text', 'content': 'Wydarzenie z BMI Cat. Szczegóły w aplikacji.'},
                'isAllDay': event['occurred_at'] is None,
                'start': {'dateTime': start.replace(tzinfo=None).isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end.replace(tzinfo=None).isoformat(), 'timeZone': 'UTC'}}

    def upsert(self, event, cat_name, remote_id, identity):
        payload = self.payload(event, cat_name)
        stable_id = hashlib.sha256(identity.encode()).hexdigest()
        if remote_id:
            response = requests.patch(f'{self.base}/{quote(remote_id, safe="")}', headers=self.headers, json=payload, timeout=12)
            if response.status_code not in (404, 410):
                response.raise_for_status()
                return remote_id
        if self.provider == 'google':
            payload['id'] = stable_id
        else:
            payload['transactionId'] = stable_id
        response = requests.post(self.base, headers=self.headers, json=payload, timeout=12)
        if self.provider == 'google' and response.status_code == 409:
            response = requests.patch(f'{self.base}/{stable_id}', headers=self.headers, json=self.payload(event, cat_name), timeout=12)
        response.raise_for_status()
        return response.json()['id']

    def remove(self, remote_id):
        response = requests.delete(f'{self.base}/{quote(remote_id, safe="")}', headers=self.headers, timeout=12)
        if response.status_code not in (404, 410):
            response.raise_for_status()
