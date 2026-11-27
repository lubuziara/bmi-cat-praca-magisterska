import time
from fastapi import HTTPException
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from sqlalchemy.exc import IntegrityError
from app.services.auth_service import AuthService


class GoogleAuthService:
    def __init__(self, auth: AuthService):
        self.auth = auth

    def reauthenticate(self, user, raw_token: str | None) -> bool:
        if not raw_token or not user.google_subject or not self.auth.settings.google_client_id:
            return False
        try:
            claims = id_token.verify_oauth2_token(raw_token, Request(), self.auth.settings.google_client_id)
        except ValueError:
            return False
        issued_at = claims.get("auth_time", claims.get("iat"))
        now = int(time.time())
        return (claims.get("email_verified") is True and claims.get("sub") == user.google_subject
                and isinstance(issued_at, (int, float))
                and now - self.auth.settings.reauth_seconds <= issued_at <= now + 60)

    def login(self, raw_token: str, request=None):
        if not self.auth.settings.google_client_id:
            raise HTTPException(503, "Logowanie Google nie jest jeszcze dostępne.")
        try:
            claims = id_token.verify_oauth2_token(raw_token, Request(), self.auth.settings.google_client_id)
        except ValueError:
            raise HTTPException(401, "Nie udało się potwierdzić konta Google.")
        if not claims.get("email_verified") or not claims.get("email") or not claims.get("sub"):
            raise HTTPException(401, "Google nie potwierdziło adresu e-mail.")
        user = self.auth.users.by_google_subject(claims["sub"])
        if not user:
            email = claims["email"].strip().lower()
            if self.auth.users.by_email(email):
                # Nie łączymy automatycznie istniejącego konta na podstawie e-maila.
                raise HTTPException(409, "To konto używa hasła. Zaloguj się e-mailem i hasłem.")
            try:
                user = self.auth.users.create(email=email, first_name=claims.get("given_name", "Opiekun")[:80],
                                               google_subject=claims["sub"], password_hash=None)
            except IntegrityError:
                self.auth.session.rollback()
                raise HTTPException(409, "Spróbuj zalogować się ponownie.")
        return self.auth.complete_primary_login(user, auth_method='google', request=request)
