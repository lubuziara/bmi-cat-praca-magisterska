import hashlib
import json
import logging
import threading
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import select
from app.database.models.calendar_connection import CalendarConnection
from app.services.calendar_oauth_service import CalendarOAuthService
from app.services.calendar_provider import CalendarProvider
from app.services.calendar_service import CalendarService


class CalendarSyncWorker:
    # Local deployment uses one API worker. Each sync owns its database session.
    def __init__(self, database, settings):
        self.database, self.settings = database, settings
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        if self.settings.calendar_token_key:
            self.thread = threading.Thread(target=self.run, daemon=True, name='calendar-sync')
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=15)

    def run(self):
        while not self.stop_event.is_set():
            try:
                with self.database.sessions() as session:
                    keys = session.execute(select(CalendarConnection.user_id, CalendarConnection.provider)).all()
                for user_id, provider in keys:
                    if self.stop_event.is_set():
                        break
                    self.sync(user_id, provider)
            except Exception:
                logging.getLogger(__name__).warning('Calendar sync iteration failed; will retry.')
            self.stop_event.wait(60)

    def sync(self, user_id, provider):
        with self.lock, self.database.sessions() as session:
            connection = session.get(CalendarConnection, (user_id, provider))
            if connection is None:
                return
            try:
                oauth = CalendarOAuthService(session, self.settings)
                remote = CalendarProvider(provider, oauth.access_token(connection))
                calendar = CalendarService(session, user_id)
                events = {event['key']: event for event in calendar.read()}
                mappings = dict(connection.mappings)
                for key, event in events.items():
                    if self.stop_event.is_set():
                        return
                    digest = hashlib.sha256(json.dumps([calendar.cat.name, event], sort_keys=True).encode()).hexdigest()
                    previous = mappings.get(key, {})
                    if previous.get('hash') == digest and not previous.get('deleted'):
                        continue
                    if not previous or previous.get('deleted'):
                        previous = {'nonce': uuid4().hex}
                        mappings[key] = previous
                        connection.mappings = dict(mappings)
                        session.commit()
                    remote_id = remote.upsert(event, calendar.cat.name, previous.get('id'), previous['nonce'])
                    mappings[key] = {'id': remote_id, 'hash': digest, 'nonce': previous['nonce']}
                    connection.mappings = dict(mappings)
                    session.commit()
                for key in set(mappings)-set(events):
                    if self.stop_event.is_set():
                        return
                    if mappings[key].get('deleted'):
                        continue
                    if mappings[key].get('id'):
                        remote.remove(mappings[key]['id'])
                    mappings[key] = {**mappings[key], 'deleted': True}
                    connection.mappings = dict(mappings)
                    session.commit()
                connection.error = None
                connection.last_sync = datetime.now(timezone.utc).isoformat()
                session.commit()
            except Exception:
                session.rollback()
                connection = session.get(CalendarConnection, (user_id, provider))
                if connection:
                    connection.error = 'Synchronizacja nie powiodła się. Ponowimy próbę; w razie potrzeby połącz konto ponownie.'
                    session.commit()
