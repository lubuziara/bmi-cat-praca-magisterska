from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base
class SecurityEvent(Base):
    __tablename__ = 'security_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[int]
    success: Mapped[bool]
    severity: Mapped[str] = mapped_column(String(16))
    client_type: Mapped[str] = mapped_column(String(16), default='other')
    device: Mapped[str] = mapped_column(String(120), default='Unknown device')
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
