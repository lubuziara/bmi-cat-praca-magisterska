import base64
import hashlib
import json
import secrets
import time
from urllib.parse import urlencode
from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy import delete
import requests
from app.database.models.calendar_connection import CalendarConnection
from app.database.models.calendar_oauth_state import CalendarOAuthState


class CalendarOAuthService:
    def __init__(self, session, settings):
        self.session = session
        self.settings = settings

    def config(self, provider):
        if provider == 'google':
            return dict(client_id=self.settings.google_calendar_client_id,
                        client_secret=self.settings.google_calendar_client_secret,
                        authorize='https://accounts.google.com/o/oauth2/v2/auth',
                        token='https://oauth2.googleapis.com/token',
                        scope='openid https://www.googleapis.com/auth/calendar.events')
        if provider == 'outlook':
            return dict(client_id=self.settings.outlook_client_id,
                        client_secret=self.settings.outlook_client_secret,
                        authorize='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                        token='https://login.microsoftonline.com/common/oauth2/v2.0/token',
                        scope='offline_access https://graph.microsoft.com/Calendars.ReadWrite')
        raise HTTPException(404, 'Nieznany dostawca kalendarza.')

    def configured(self, provider):
        config = self.config(provider)
        return bool(config['client_id'] and config['client_secret'] and self.settings.calendar_token_key)

    def cipher(self):
        return Fernet(self.settings.calendar_token_key.encode())

    def redirect(self, provider):
        return f'{self.settings.api_base_url.rstrip("/")}/api/auth/calendar-connections/{provider}/callback'

    def start(self, provider, user_id):
        if not self.configured(provider):
            raise HTTPException(503, 'Uzupełnij konfigurację OAuth kalendarza w głównym .env i uruchom ponownie API.')
        config = self.config(provider)
        state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        self.session.execute(delete(CalendarOAuthState).where(CalendarOAuthState.expires < int(time.time())))
        self.session.add(CalendarOAuthState(digest=hashlib.sha256(state.encode()).hexdigest(), user_id=user_id,
            provider=provider, verifier=self.cipher().encrypt(verifier.encode()).decode(), expires=int(time.time())+600))
        self.session.commit()
        query = dict(client_id=config['client_id'], redirect_uri=self.redirect(provider), response_type='code',
                     scope=config['scope'], state=state, code_challenge_method='S256',
                     code_challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('='))
        if provider == 'google':
            query.update(access_type='offline', prompt='consent')
        else:
            query.update(response_mode='query', prompt='select_account')
        return {'url': config['authorize']+'?'+urlencode(query)}

    def finish(self, provider, state, code, error=None):
        self.config(provider)
        digest = hashlib.sha256(state.encode()).hexdigest()
        row = self.session.get(CalendarOAuthState, digest)
        if not row or row.provider != provider or row.expires < time.time():
            raise HTTPException(400, 'Połączenie wygasło albo zostało już wykorzystane. Spróbuj ponownie w aplikacji.')
        verifier, user_id = self.cipher().decrypt(row.verifier.encode()).decode(), row.user_id
        consumed = self.session.execute(delete(CalendarOAuthState).where(CalendarOAuthState.digest == digest))
        self.session.commit()
        if consumed.rowcount != 1:
            raise HTTPException(400, 'Połączenie zostało już wykorzystane.')
        if error or not code:
            raise HTTPException(400, 'Nie udzielono zgody na połączenie kalendarza.')
        config = self.config(provider)
        try:
            response = requests.post(config['token'], data={
                'client_id': config['client_id'], 'client_secret': config['client_secret'],
                'grant_type': 'authorization_code', 'code': code,
                'redirect_uri': self.redirect(provider), 'code_verifier': verifier}, timeout=12)
            response.raise_for_status()
            token = response.json()
            if not token.get('refresh_token') or not token.get('access_token'):
                raise ValueError('missing offline access')
            identity_url = ('https://openidconnect.googleapis.com/v1/userinfo' if provider == 'google'
                            else 'https://graph.microsoft.com/v1.0/me/calendar')
            identity = requests.get(identity_url, headers={'Authorization': f"Bearer {token['access_token']}"}, timeout=12)
            identity.raise_for_status()
            token['account_key'] = identity.json()['sub' if provider == 'google' else 'id']
        except (requests.RequestException, ValueError, KeyError):
            raise HTTPException(502, 'Nie udało się połączyć kalendarza. Spróbuj ponownie i zaakceptuj dostęp offline.') from None
        token['expires_at'] = int(time.time()) + int(token.get('expires_in', 3600))
        connection = self.session.get(CalendarConnection, (user_id, provider))
        if connection is None:
            connection = CalendarConnection(user_id=user_id, provider=provider, mappings={})
            self.session.add(connection)
        else:
            old = json.loads(self.cipher().decrypt(connection.tokens.encode()))
            if old.get('account_key') != token['account_key']:
                connection.mappings = {}
        connection.tokens = self.cipher().encrypt(json.dumps(token).encode()).decode()
        connection.error = None
        self.session.commit()

    def access_token(self, connection):
        token = json.loads(self.cipher().decrypt(connection.tokens.encode()))
        if token['expires_at'] > time.time()+60:
            return token['access_token']
        config = self.config(connection.provider)
        response = requests.post(config['token'], data={
            'client_id': config['client_id'], 'client_secret': config['client_secret'],
            'grant_type': 'refresh_token', 'refresh_token': token['refresh_token'],
        }, timeout=12)
        response.raise_for_status()
        updated = response.json()
        token.update(updated)
        token['expires_at'] = int(time.time())+int(updated.get('expires_in', 3600))
        connection.tokens = self.cipher().encrypt(json.dumps(token).encode()).decode()
        self.session.commit()
        return token['access_token']
