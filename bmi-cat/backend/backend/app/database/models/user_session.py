from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class UserSession(Base):
    __tablename__ = 'user_sessions'
    family_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    created_at: Mapped[int]
    last_activity_at: Mapped[int]
    expires_at: Mapped[int]
    revoked_at: Mapped[int | None] = mapped_column(nullable=True)
    client_type: Mapped[str] = mapped_column(String(16), default='other')
    device: Mapped[str] = mapped_column(String(120), default='Unknown device')
    auth_method: Mapped[str] = mapped_column(String(16), default='password')
    mfa_used: Mapped[bool] = mapped_column(default=False)
