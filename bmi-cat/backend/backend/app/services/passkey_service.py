import base64, json, secrets, time
from urllib.parse import urlparse
from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from webauthn import generate_authentication_options, generate_registration_options, options_to_json, verify_authentication_response, verify_registration_response
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, UserVerificationRequirement
from app.database.models.passkey import Passkey, PasskeyChallenge
from app.database.models.user import User
from app.security.token_digest import token_digest
from app.services.security_event_service import SecurityEventService

def _b64(value): return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
def _challenge(credential):
    try: return json.loads(_b64(credential['response']['clientDataJSON']))['challenge']
    except (KeyError, ValueError, TypeError): raise HTTPException(400, 'Nieprawidłowa odpowiedź passkey.')

def challenge_fingerprint(credential):
    return token_digest(_challenge(credential))

class PasskeyService:
    def __init__(self, session, settings): self.session, self.settings = session, settings
    def _config(self):
        origin = urlparse(self.settings.webauthn_origin)
        development_origin = (not self.settings.cookie_secure and origin.scheme == 'http' and origin.hostname == 'localhost')
        secure_origin = self.settings.cookie_secure and origin.scheme == 'https'
        rp_matches_origin = origin.hostname == self.settings.webauthn_rp_id or (origin.hostname or '').endswith('.' + self.settings.webauthn_rp_id)
        if not self.settings.webauthn_rp_id or not self.settings.webauthn_origin or not (secure_origin or development_origin) or not rp_matches_origin:
            raise HTTPException(503, 'Passkeys nie są skonfigurowane.')
    def _origins(self): return [self.settings.webauthn_origin, *self.settings.webauthn_android_origins]
    def _issue(self, user_id, kind):
        raw = secrets.token_bytes(32); self.session.add(PasskeyChallenge(digest=token_digest(base64.urlsafe_b64encode(raw).rstrip(b'=').decode()), user_id=user_id, kind=kind, expires_at=int(time.time()) + 300)); self.session.commit(); return raw
    def _consume(self, credential, kind, user_id=None):
        raw = _challenge(credential); record = self.session.get(PasskeyChallenge, token_digest(raw)); now = int(time.time())
        if not record or record.kind != kind or record.used_at is not None or record.expires_at <= now or (user_id is not None and record.user_id != user_id): raise HTTPException(401, 'Weryfikacja passkey wygasła.')
        claimed = self.session.execute(update(PasskeyChallenge).where(PasskeyChallenge.digest == record.digest, PasskeyChallenge.used_at.is_(None)).values(used_at=now))
        if not claimed.rowcount: self.session.rollback(); raise HTTPException(401, 'Weryfikacja passkey wygasła.')
        self.session.commit()
        return _b64(raw)
    def registration_options(self, user):
        self._config(); challenge = self._issue(user.id, 'register'); keys = self.session.scalars(select(Passkey).where(Passkey.user_id == user.id)).all()
        return json.loads(options_to_json(generate_registration_options(rp_id=self.settings.webauthn_rp_id, rp_name=self.settings.webauthn_rp_name, user_id=str(user.id).encode(), user_name=user.email, user_display_name=user.first_name, challenge=challenge, exclude_credentials=[PublicKeyCredentialDescriptor(id=k.credential_id) for k in keys], timeout=300000)))
    def registration_verify(self, user, credential, name=None):
        self._config(); challenge = self._consume(credential, 'register', user.id)
        try: verified = verify_registration_response(credential=credential, expected_challenge=challenge, expected_rp_id=self.settings.webauthn_rp_id, expected_origin=self._origins(), require_user_verification=True)
        except Exception: self.session.rollback(); raise HTTPException(401, 'Nie udało się potwierdzić passkey.')
        try:
            self.session.add(Passkey(user_id=user.id, credential_id=verified.credential_id, public_key=verified.credential_public_key, sign_count=verified.sign_count, created_at=int(time.time()), name=name))
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise HTTPException(409, 'Ten passkey jest już przypisany do innego konta.')
        SecurityEventService(self.session).record(user.id, 'passkey_added'); self.session.commit(); return {'id': self.session.scalar(select(Passkey.id).where(Passkey.credential_id == verified.credential_id))}
    def login_options(self):
        self._config(); challenge = self._issue(None, 'login')
        return json.loads(options_to_json(generate_authentication_options(rp_id=self.settings.webauthn_rp_id, challenge=challenge, timeout=300000, user_verification=UserVerificationRequirement.REQUIRED)))
    def step_up_options(self, user, challenge):
        self._config(); keys = self.session.scalars(select(Passkey).where(Passkey.user_id == user.id)).all()
        return json.loads(options_to_json(generate_authentication_options(rp_id=self.settings.webauthn_rp_id, challenge=challenge, timeout=300000, allow_credentials=[PublicKeyCredentialDescriptor(id=k.credential_id) for k in keys], user_verification=UserVerificationRequirement.REQUIRED)))
    def step_up_verify(self, user, credential, challenge):
        self._config()
        try: key = self.session.scalar(select(Passkey).where(Passkey.credential_id == _b64(credential['rawId']), Passkey.user_id == user.id))
        except (KeyError, ValueError): key = None
        if not key: raise HTTPException(401, 'Nie udało się potwierdzić passkey.')
        try: verified = verify_authentication_response(credential=credential, expected_challenge=challenge, expected_rp_id=self.settings.webauthn_rp_id, expected_origin=self._origins(), credential_public_key=key.public_key, credential_current_sign_count=key.sign_count, require_user_verification=True)
        except Exception: self.session.rollback(); raise HTTPException(401, 'Nie udało się potwierdzić passkey.')
        key.sign_count, key.last_used_at = verified.new_sign_count, int(time.time()); self.session.commit()
    def login_verify(self, credential, request=None):
        self._config(); challenge = self._consume(credential, 'login')
        try: key = self.session.scalar(select(Passkey).where(Passkey.credential_id == _b64(credential['rawId'])))
        except (KeyError, ValueError): key = None
        if not key: self.session.rollback(); raise HTTPException(401, 'Nie udało się potwierdzić passkey.')
        try: verified = verify_authentication_response(credential=credential, expected_challenge=challenge, expected_rp_id=self.settings.webauthn_rp_id, expected_origin=self._origins(), credential_public_key=key.public_key, credential_current_sign_count=key.sign_count, require_user_verification=True)
        except Exception: self.session.rollback(); raise HTTPException(401, 'Nie udało się potwierdzić passkey.')
        key.sign_count, key.last_used_at = verified.new_sign_count, int(time.time()); user = self.session.get(User, key.user_id); SecurityEventService(self.session).record(user.id, 'passkey_login_success', request=request); self.session.commit(); return user
    def list(self, user): return [{'id': k.id, 'name': k.name, 'created_at': k.created_at, 'last_used_at': k.last_used_at} for k in self.session.scalars(select(Passkey).where(Passkey.user_id == user.id))]
    def delete(self, user, passkey_id):
        key = self.session.scalar(select(Passkey).where(Passkey.id == passkey_id, Passkey.user_id == user.id))
        if not key:
            raise HTTPException(404, 'Nie znaleziono passkey.')
        remaining = self.session.scalar(select(Passkey.id).where(Passkey.user_id == user.id, Passkey.id != passkey_id).limit(1))
        if not remaining and not (user.password_hash or user.google_subject):
            raise HTTPException(409, 'Nie można usunąć ostatniego passkey bez innej metody logowania lub odzyskania dostępu.')
        self.session.delete(key); SecurityEventService(self.session).record(user.id, 'passkey_removed')
        self.session.commit()
        return {'message': 'Passkey usunięty.'}
