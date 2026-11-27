from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class UserMfa(Base):
    __tablename__ = "user_mfa"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    encrypted_secret: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(default=False)
    last_totp_counter: Mapped[int | None] = mapped_column(nullable=True)


class MfaSetup(Base):
    __tablename__ = "mfa_setups"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    encrypted_secret: Mapped[str] = mapped_column(String(512))
    expires_at: Mapped[int]


class MfaChallenge(Base):
    __tablename__ = "mfa_challenges"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[int]
    used_at: Mapped[int | None] = mapped_column(nullable=True)


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    generation: Mapped[int]
    used_at: Mapped[int | None] = mapped_column(nullable=True)
