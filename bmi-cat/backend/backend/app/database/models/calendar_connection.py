from sqlalchemy import ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class CalendarConnection(Base):
    __tablename__ = 'calendar_connections'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    provider: Mapped[str] = mapped_column(String(16), primary_key=True)
    tokens: Mapped[str] = mapped_column(Text)
    mappings: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_sync: Mapped[str | None] = mapped_column(String(40), nullable=True)
