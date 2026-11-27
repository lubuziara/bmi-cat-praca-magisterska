from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class VerificationChallenge(Base):
    __tablename__ = "verification_challenges"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    channel: Mapped[str] = mapped_column(String(8), primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[int]
    sent_at: Mapped[int]
    attempts: Mapped[int] = mapped_column(default=0)
