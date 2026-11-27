from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class CalendarOAuthState(Base):
    __tablename__ = 'calendar_oauth_states'
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    provider: Mapped[str] = mapped_column(String(16))
    verifier: Mapped[str] = mapped_column(Text)
    expires: Mapped[int]
