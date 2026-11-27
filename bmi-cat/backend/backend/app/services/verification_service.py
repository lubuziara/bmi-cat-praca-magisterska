import secrets
import time
from fastapi import HTTPException
from app.database.models.owner_profile import OwnerProfile
from app.database.models.user import User
from app.database.models.verification_challenge import VerificationChallenge
from app.security.passwords import password_hasher


class VerificationService:
    def __init__(self, session, user_id: int):
        self.session = session
        self.user_id = user_id
        self.profile = session.get(OwnerProfile, user_id)
        if not self.profile:
            raise HTTPException(409, "To konto nie ma jeszcze pełnego profilu rejestracyjnego.")

    def status(self):
        return {"email_verified": self.profile.email_verified, "phone_verified": self.profile.phone_verified,
                "registration_verified": self.profile.email_verified and self.profile.phone_verified}

    def send(self, channel: str, mailer, sms):
        if getattr(self.profile, f"{channel}_verified"):
            return self.status()
        now = int(time.time())
        key = (self.user_id, channel)
        challenge = self.session.get(VerificationChallenge, key)
        if challenge and challenge.sent_at > now - 60:
            raise HTTPException(429, "Odczekaj minutę przed wysłaniem kolejnego kodu.", headers={"Retry-After": "60"})
        code = f"{secrets.randbelow(1000000):06d}"
        if not challenge:
            challenge = VerificationChallenge(user_id=self.user_id, channel=channel)
            self.session.add(challenge)
        challenge.code_hash = password_hasher.hash(code)
        challenge.sent_at = now
        challenge.expires_at = now + 600
        challenge.attempts = 0
        self.session.flush()
        try:
            if channel == "email":
                mailer.send_verification(self.session.get(User, self.user_id).email, code)
            else:
                sms.send(self.profile.phone, code)
        except OSError:
            self.session.rollback()
            raise HTTPException(503, "Nie udało się wysłać kodu. Spróbuj później.")
        self.session.commit()
        return {**self.status(), "message": "Kod został wysłany. Jest ważny przez 10 minut."}

    def confirm(self, data):
        challenge = self.session.get(VerificationChallenge, (self.user_id, data.channel))
        if not challenge or challenge.expires_at <= int(time.time()):
            raise HTTPException(400, "Kod wygasł lub został już użyty. Wyślij nowy kod.")
        if challenge.attempts >= 5:
            raise HTTPException(429, "Wykorzystano limit prób. Wyślij nowy kod.")
        challenge.attempts += 1
        if not password_hasher.verify(data.code, challenge.code_hash):
            self.session.commit()
            raise HTTPException(400, "Nieprawidłowy kod.")
        setattr(self.profile, f"{data.channel}_verified", True)
        self.session.delete(challenge)
        self.session.commit()
        return self.status()
