from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    family_id: Mapped[str] = mapped_column(String(64), index=True)
    expires_at: Mapped[int]
    used_at: Mapped[int | None] = mapped_column(nullable=True)
    revoked_at: Mapped[int | None] = mapped_column(nullable=True)
