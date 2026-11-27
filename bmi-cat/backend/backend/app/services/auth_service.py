from datetime import date
from app.database.models.owner_profile import OwnerProfile
from app.database.models.cat import Cat
import secrets
import base64
import time
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import delete, update, select, or_
from sqlalchemy.exc import IntegrityError
from app.config import Settings
from app.database.crud.user_repository import UserRepository
from app.database.models.auth_token import AuthToken
from app.database.models.access_token import AccessToken
from app.database.models.refresh_token import RefreshToken
from app.database.models.user import User
from app.database.models.user_session import UserSession
from app.services.security_event_service import SecurityEventService
from app.services.risk_engine import RiskEngine
from app.security.passwords import password_hasher, dummy_hash
from app.security.token_digest import token_digest
from app.security import totp
from app.services.password_breach_service import PasswordBreachService
from app.database.models.user_mfa import MfaChallenge, MfaSetup, RecoveryCode, UserMfa
from app.database.models.step_up_challenge import StepUpChallenge


class AuthService:
    def __init__(self, session, settings: Settings):
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)
        self.password_breach = PasswordBreachService(settings)

    def register(self, data):
        self.password_breach.validate(data.password)
        try:
            user = self.users.create(email=str(data.email), first_name=data.first_name,
                              password_hash=password_hasher.hash(data.password))
            self.session.add(OwnerProfile(user_id=user.id, last_name=data.last_name, gender=data.gender,
                birth_date=data.birth_date, phone=data.phone))
            self.session.add(Cat(owner_id=user.id, name=data.cat.name, gender=data.cat.gender,
                birth_date=data.cat.birth_date, estimated_age_months=data.cat.estimated_age_months,
                age_recorded_on=date.today(), avatar=data.cat.avatar.model_dump()))
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise HTTPException(409, "Nie można utworzyć konta z tym adresem. Zaloguj się lub odzyskaj hasło.")
        return {**self.start_session(user), "message": "Konto utworzone. Potwierdź e-mail i telefon."}

    def issue_token(self, user_id: int, purpose: str, lifetime: int):
        now = int(time.time())
        self.session.execute(delete(AuthToken).where(AuthToken.expires_at <= now))
        raw = secrets.token_urlsafe(32)
        self.session.add(AuthToken(digest=token_digest(raw), user_id=user_id,
                                   purpose=purpose, expires_at=now + lifetime))
        self.session.flush()
        return raw

    def login(self, data, request=None):
        user = self.users.by_email(str(data.email))
        valid = password_hasher.verify(data.password, user.password_hash if user and user.password_hash else dummy_hash)
        if not user or not user.password_hash or not valid:
            if user: SecurityEventService(self.session).record(user.id, 'login_failed', success=False, severity='warning', request=request); self.session.commit()
            raise HTTPException(401, "Nieprawidłowy e-mail lub hasło.")
        result = self.complete_primary_login(user, auth_method='password', request=request)
        SecurityEventService(self.session).record(user.id, 'login_success', request=request)
        self.session.commit()
        return result

    def complete_primary_login(self, user, auth_method='password', request=None):
        risk = RiskEngine(self.session, self.settings).evaluate(user.id, request=request, auth_method=auth_method)
        if risk.level != 'low':
            events = SecurityEventService(self.session)
            events.record(user.id, f'risk_{risk.level}_detected', success=False, severity='critical' if risk.level == 'critical' else 'warning', metadata={'risk_level': risk.level, 'signals': ','.join(risk.signals)}, request=request)
            if risk.action == 'block':
                self.session.commit()
                raise HTTPException(401, 'Logowanie chwilowo niedostępne. Spróbuj ponownie później.')
            events.record(user.id, 'step_up_auth_required', severity='warning', metadata={'risk_level': risk.level}, request=request)
            return self._start_step_up(user)
        mfa = self.session.get(UserMfa, user.id)
        if mfa and mfa.enabled:
            raw = secrets.token_urlsafe(32)
            self.session.add(MfaChallenge(digest=token_digest(raw), user_id=user.id,
                                          expires_at=int(time.time()) + 300))
            self.session.commit()
            return {"mfa_required": True, "mfa_challenge": raw, "expires_in": 300}
        return self.start_session(user)

    def _start_step_up(self, user):
        mfa = self.session.get(UserMfa, user.id)
        methods = ['passkey']
        if mfa and mfa.enabled:
            methods.extend(['totp', 'recovery_code'])
        raw = secrets.token_urlsafe(32)
        self.session.add(StepUpChallenge(digest=token_digest(raw), user_id=user.id,
                                         methods=methods, expires_at=int(time.time()) + 300))
        self.session.commit()
        return {'step_up_required': True, 'step_up_challenge': raw, 'methods': methods, 'expires_in': 300}

    def _step_up(self, raw: str, method: str, consume=False):
        record = self.session.get(StepUpChallenge, token_digest(raw)); now = int(time.time())
        if not record or record.used_at is not None or record.expires_at <= now or method not in record.methods:
            raise HTTPException(401, 'Dodatkowa weryfikacja wygasła.')
        user = self.session.get(User, record.user_id)
        if not user: raise HTTPException(401, 'Dodatkowa weryfikacja wygasła.')
        if consume:
            claimed = self.session.execute(update(StepUpChallenge).where(StepUpChallenge.digest == record.digest, StepUpChallenge.used_at.is_(None), StepUpChallenge.expires_at > now).values(used_at=now))
            if not claimed.rowcount:
                self.session.rollback(); raise HTTPException(401, 'Dodatkowa weryfikacja wygasła.')
            self.session.commit()
        return user

    @staticmethod
    def _step_up_bytes(raw: str) -> bytes:
        return base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4))

    def step_up_passkey_options(self, raw: str):
        from app.services.passkey_service import PasskeyService
        return PasskeyService(self.session, self.settings).step_up_options(self._step_up(raw, 'passkey'), self._step_up_bytes(raw))

    def step_up_passkey_verify(self, raw: str, credential):
        from app.services.passkey_service import PasskeyService
        user = self._step_up(raw, 'passkey', consume=True)
        try:
            PasskeyService(self.session, self.settings).step_up_verify(user, credential, self._step_up_bytes(raw))
        except HTTPException:
            SecurityEventService(self.session).record(user.id, 'step_up_auth_failed', success=False, severity='warning'); self.session.commit(); raise
        SecurityEventService(self.session).record(user.id, 'step_up_auth_success'); self.session.commit()
        return self.start_session(user)

    def _fernet(self):
        if not self.settings.mfa_totp_encryption_key:
            raise HTTPException(503, "2FA nie jest skonfigurowane.")
        try:
            return Fernet(self.settings.mfa_totp_encryption_key.encode())
        except (ValueError, TypeError):
            raise HTTPException(503, "2FA nie jest skonfigurowane.")

    def _secret(self, encrypted: str) -> str:
        try:
            return self._fernet().decrypt(encrypted.encode()).decode()
        except (InvalidToken, UnicodeDecodeError):
            raise HTTPException(503, "2FA nie jest skonfigurowane.")

    def _recovery_codes(self, user_id: int, generation: int) -> list[str]:
        codes = [secrets.token_urlsafe(16) for _ in range(10)]
        self.session.add_all(RecoveryCode(digest=token_digest(code), user_id=user_id,
                                         generation=generation) for code in codes)
        return codes

    def mfa_status(self, user):
        mfa = self.session.get(UserMfa, user.id)
        return {"enabled": bool(mfa and mfa.enabled)}

    def mfa_setup(self, user, password=None, google_id_token=None, code=None):
        self._require_reauthentication(user, password, google_id_token, code)
        raw = secrets.token_urlsafe(32)
        secret = totp.new_secret()
        self.session.add(MfaSetup(digest=token_digest(raw), user_id=user.id,
                                  encrypted_secret=self._fernet().encrypt(secret.encode()).decode(),
                                  expires_at=int(time.time()) + self.settings.reauth_seconds))
        self.session.commit()
        issuer = "BMICat"
        return {"setup_challenge": raw,
                "otpauth_uri": f"otpauth://totp/{issuer}:{user.email}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"}

    def mfa_confirm(self, user, setup_challenge: str, code: str):
        record = self.session.get(MfaSetup, token_digest(setup_challenge))
        if not record or record.user_id != user.id or record.expires_at <= int(time.time()):
            raise HTTPException(401, "Konfiguracja 2FA wygasła.")
        secret = self._secret(record.encrypted_secret)
        if totp.verify(secret, code) is None:
            raise HTTPException(401, "Nieprawidłowy kod 2FA.")
        existing = self.session.get(UserMfa, user.id)
        if existing:
            existing.encrypted_secret = self._fernet().encrypt(secret.encode()).decode()
            existing.enabled = True
            existing.last_totp_counter = None
        else:
            self.session.add(UserMfa(user_id=user.id, encrypted_secret=self._fernet().encrypt(secret.encode()).decode(), enabled=True))
        self.session.execute(delete(MfaSetup).where(MfaSetup.user_id == user.id))
        self.session.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
        codes = self._recovery_codes(user.id, int(time.time()))
        self.session.commit()
        SecurityEventService(self.session).record(user.id, 'mfa_enabled')
        self.session.commit()
        return {"recovery_codes": codes}

    def _verify_mfa_code(self, user, code: str, methods=None) -> bool:
        mfa = self.session.get(UserMfa, user.id)
        if not mfa or not mfa.enabled:
            return False
        methods = methods or ('totp', 'recovery_code')
        counter = totp.verify(self._secret(mfa.encrypted_secret), code) if 'totp' in methods else None
        if counter is not None:
            claimed = self.session.execute(update(UserMfa).where(
                UserMfa.user_id == user.id,
                or_(UserMfa.last_totp_counter.is_(None), UserMfa.last_totp_counter < counter),
            ).values(last_totp_counter=counter))
            if not claimed.rowcount:
                self.session.expire(mfa)
                return False
            return True
        recovery = self.session.get(RecoveryCode, token_digest(code)) if 'recovery_code' in methods else None
        if recovery and recovery.user_id == user.id and recovery.used_at is None:
            recovery.used_at = int(time.time())
            SecurityEventService(self.session).record(user.id, 'recovery_code_used')
            return True
        return False

    def step_up_mfa_verify(self, raw: str, code: str):
        record = self.session.get(StepUpChallenge, token_digest(raw))
        methods = record.methods if record else []
        method = 'totp' if 'totp' in methods else 'recovery_code'
        user = self._step_up(raw, method, consume=True)
        if not self._verify_mfa_code(user, code, methods):
            self.session.rollback(); SecurityEventService(self.session).record(user.id, 'mfa_failed', success=False, severity='warning'); SecurityEventService(self.session).record(user.id, 'step_up_auth_failed', success=False, severity='warning'); self.session.commit(); raise HTTPException(401, 'Nieprawidłowy kod 2FA.')
        SecurityEventService(self.session).record(user.id, 'step_up_auth_success'); self.session.commit()
        return self.start_session(user)

    def mfa_verify_login(self, challenge: str, code: str):
        record = self.session.get(MfaChallenge, token_digest(challenge))
        now = int(time.time())
        if not record or record.used_at is not None or record.expires_at <= now:
            raise HTTPException(401, "Weryfikacja 2FA wygasła.")
        user = self.session.get(User, record.user_id)
        if not user or not self._verify_mfa_code(user, code):
            self.session.rollback()
            if user:
                SecurityEventService(self.session).record(user.id, 'mfa_failed', success=False, severity='warning')
                SecurityEventService(self.session).record(user.id, 'step_up_auth_failed', success=False, severity='warning')
                self.session.commit()
            raise HTTPException(401, "Nieprawidłowy kod 2FA.")
        record.used_at = now
        SecurityEventService(self.session).record(user.id, 'step_up_auth_success')
        self.session.commit()
        return self.start_session(user)

    def mfa_disable(self, user, password: str | None, google_id_token: str | None, code: str | None):
        self._require_reauthentication(user, password, google_id_token, code)
        self.session.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
        self.session.execute(delete(UserMfa).where(UserMfa.user_id == user.id))
        self.session.commit()
        SecurityEventService(self.session).record(user.id, 'mfa_disabled')
        self.session.commit()
        return {"message": "2FA wyłączone."}

    def mfa_regenerate_recovery(self, user, password: str | None, google_id_token: str | None, code: str | None):
        self._require_reauthentication(user, password, google_id_token, code)
        self.session.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
        codes = self._recovery_codes(user.id, int(time.time()))
        self.session.commit()
        SecurityEventService(self.session).record(user.id, 'recovery_codes_regenerated'); self.session.commit()
        return {"recovery_codes": codes}

    def _require_reauthentication(self, user, password: str | None, google_id_token: str | None, code: str | None):
        if user.password_hash:
            authenticated = bool(password) and password_hasher.verify(password, user.password_hash)
        else:
            from app.services.google_auth_service import GoogleAuthService
            authenticated = GoogleAuthService(self).reauthenticate(user, google_id_token)
        if not authenticated:
            raise HTTPException(401, "Ponownie potwierdź tożsamość.")
        mfa = self.session.get(UserMfa, user.id)
        if mfa and mfa.enabled and (not code or not self._verify_mfa_code(user, code)):
            self.session.rollback()
            raise HTTPException(401, "Ponownie potwierdź tożsamość.")

    def start_session(self, user):
        tokens = self.issue_session_tokens(user.id, secrets.token_urlsafe(24))
        self.session.commit()
        return {**tokens, "user": self.user_summary(user)}

    def issue_session_tokens(self, user_id: int, family_id: str):
        now = int(time.time())
        if not self.session.get(UserSession, family_id):
            self.session.add(UserSession(family_id=family_id, user_id=user_id, created_at=now, last_activity_at=now, expires_at=now + self.settings.refresh_seconds))
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        self.session.add(AccessToken(digest=token_digest(access_token), user_id=user_id,
                                     family_id=family_id, expires_at=now + self.settings.access_seconds))
        self.session.add(RefreshToken(digest=token_digest(refresh_token), user_id=user_id,
                                      family_id=family_id, expires_at=now + self.settings.refresh_seconds))
        self.session.flush()
        return {"access_token": access_token, "token_type": "bearer",
                "expires_in": self.settings.access_seconds, "refresh_token": refresh_token,
                "refresh_expires_in": self.settings.refresh_seconds}

    def current_user(self, raw: str):
        token = self.session.get(AccessToken, token_digest(raw))
        if not token or token.expires_at <= int(time.time()):
            raise HTTPException(401, "Sesja wygasła. Zaloguj się ponownie.")
        user = self.session.get(User, token.user_id)
        if not user:
            raise HTTPException(401, "Zaloguj się ponownie.")
        return self.user_summary(user)

    def user_for_access(self, raw: str):
        token = self.session.get(AccessToken, token_digest(raw))
        if not token or token.expires_at <= int(time.time()):
            raise HTTPException(401, "Sesja wygasła. Zaloguj się ponownie.")
        user = self.session.get(User, token.user_id)
        if not user:
            raise HTTPException(401, "Zaloguj się ponownie.")
        return user

    def logout(self, raw: str):
        token = self.session.get(AccessToken, token_digest(raw))
        if token:
            SecurityEventService(self.session).record(token.user_id, 'logout', session_id=token.family_id)
            self.revoke_family(token.family_id)
        self.session.commit()
        return {"message": "Wylogowano."}

    def logout_refresh(self, raw: str):
        token = self.session.get(RefreshToken, token_digest(raw))
        if token:
            SecurityEventService(self.session).record(token.user_id, 'logout', session_id=token.family_id)
            self.revoke_family(token.family_id)
        self.session.commit()
        return {"message": "Wylogowano."}

    def refresh_session(self, raw: str):
        now = int(time.time())
        digest = token_digest(raw)
        token = self.session.get(RefreshToken, digest)
        if not token:
            raise HTTPException(401, "Sesja wygasła. Zaloguj się ponownie.")
        claimed = self.session.execute(update(RefreshToken).where(
            RefreshToken.digest == digest, RefreshToken.used_at.is_(None),
            RefreshToken.revoked_at.is_(None), RefreshToken.expires_at > now
        ).values(used_at=now))
        if not claimed.rowcount:
            if token.used_at is not None:
                SecurityEventService(self.session).record(token.user_id, 'refresh_token_reuse_detected', session_id=token.family_id, success=False, severity='critical')
                self.revoke_family(token.family_id, now)
                self.session.commit()
            else:
                self.session.rollback()
            raise HTTPException(401, "Sesja wygasła. Zaloguj się ponownie.")
        tokens = self.issue_session_tokens(token.user_id, token.family_id)
        self.session.commit()
        return tokens

    def revoke_family(self, family_id: str, now: int | None = None):
        now = now or int(time.time())
        self.session.execute(delete(AccessToken).where(AccessToken.family_id == family_id))
        self.session.execute(update(RefreshToken).where(
            RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None)
        ).values(revoked_at=now))
        record = self.session.get(UserSession, family_id)
        if record: record.revoked_at = now

    def sessions(self, raw):
        token = self.session.get(AccessToken, token_digest(raw))
        if not token: raise HTTPException(401, 'Sesja wygasła. Zaloguj się ponownie.')
        records = self.session.scalars(select(UserSession).where(UserSession.user_id == token.user_id)).all()
        return [{'id': s.family_id, 'created_at': s.created_at, 'last_activity_at': s.last_activity_at, 'client_type': s.client_type, 'device': s.device, 'auth_method': s.auth_method, 'mfa_used': s.mfa_used, 'is_current': s.family_id == token.family_id} for s in records]
    def revoke_session(self, raw, family_id):
        token = self.session.get(AccessToken, token_digest(raw))
        record = self.session.get(UserSession, family_id)
        if not token or not record or record.user_id != token.user_id: raise HTTPException(404, 'Nie znaleziono sesji.')
        SecurityEventService(self.session).record(token.user_id, 'session_revoked', session_id=family_id); self.revoke_family(family_id); self.session.commit()
    def revoke_others(self, raw):
        token = self.session.get(AccessToken, token_digest(raw))
        if not token: raise HTTPException(401, 'Sesja wygasła. Zaloguj się ponownie.')
        for family_id in self.session.scalars(select(UserSession.family_id).where(UserSession.user_id == token.user_id, UserSession.family_id != token.family_id, UserSession.revoked_at.is_(None))): self.revoke_family(family_id)
        SecurityEventService(self.session).record(token.user_id, 'other_sessions_revoked', session_id=token.family_id)
        self.session.commit()

    def revoke_all_sessions(self, user_id: int):
        self.session.execute(delete(AccessToken).where(AccessToken.user_id == user_id))
        self.session.execute(update(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        ).values(revoked_at=int(time.time())))

    def request_reset(self, data, mailer):
        user = self.users.by_email(str(data.email))
        if user:
            self.users.revoke_tokens(user.id, "reset")
            token = self.issue_token(user.id, "reset", self.settings.reset_seconds)
            # Błąd poczty nie ujawnia istnienia konta. Transakcja wycofuje nowy token.
            try:
                mailer.send_reset(user.email, token)
                self.session.commit()
            except (OSError, ValueError):
                self.session.rollback()
                import logging
                logging.getLogger(__name__).error("Nie udało się dostarczyć wiadomości resetowania hasła.")
        return {"message": "Jeśli konto istnieje, otrzymasz wiadomość z linkiem do zmiany hasła."}

    def reset_password(self, data):
        self.password_breach.validate(data.password)
        # DELETE ... RETURNING konsumuje token atomowo również przy równoległych żądaniach.
        user_id = self.session.scalar(delete(AuthToken).where(
            AuthToken.digest == token_digest(data.token), AuthToken.purpose == "reset",
            AuthToken.expires_at > int(time.time())).returning(AuthToken.user_id))
        if user_id is None:
            self.session.rollback()
            raise HTTPException(400, "Link wygasł lub został już użyty. Poproś o nowy.")
        user = self.session.get(User, user_id)
        user.password_hash = password_hasher.hash(data.password)
        self.users.revoke_tokens(user_id)
        self.revoke_all_sessions(user_id)
        SecurityEventService(self.session).record(user_id, 'password_changed')
        SecurityEventService(self.session).record(user_id, 'password_reset_completed'); self.session.commit()
        return {"message": "Hasło zostało zmienione. Zaloguj się nowym hasłem."}

    def user_summary(self, user):
        profile = self.session.get(OwnerProfile, user.id)
        return {"id": user.id, "first_name": user.first_name, "email": user.email,
                "profile_complete": profile is not None,
                "registration_verified": bool(profile and profile.email_verified and profile.phone_verified)}
