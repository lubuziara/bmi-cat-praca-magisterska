
from app.database.models.calendar_connection import CalendarConnection
from app.database.models.calendar_oauth_state import CalendarOAuthState
from app.database.models.calendar_record import CalendarRecord
from app.database.models.medical_document import MedicalDocument
from app.database.models.app_preference import AppPreference
from app.database.models.meal_entry import MealEntry
from app.database.models.owner_profile import OwnerProfile
from app.database.models.cat import Cat
from app.database.models.verification_challenge import VerificationChallenge
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.database.models.user import User
from app.database.models.auth_token import AuthToken
from app.database.models.access_token import AccessToken
from app.database.models.refresh_token import RefreshToken
from app.database.models.user_mfa import UserMfa, MfaSetup, MfaChallenge, RecoveryCode
from app.database.models.passkey import Passkey, PasskeyChallenge
from app.database.models.step_up_challenge import StepUpChallenge
from app.database.models.user_session import UserSession
from app.database.models.security_event import SecurityEvent


class Database:
    def __init__(self, url: str):
        kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, **kwargs)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def initialize(self):
        # Pierwsza, lokalna karta. Kolejne zmiany schematu powinny używać migracji.
        Base.metadata.create_all(self.engine)

