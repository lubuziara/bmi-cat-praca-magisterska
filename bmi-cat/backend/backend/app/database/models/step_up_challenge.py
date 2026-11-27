from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class StepUpChallenge(Base):
    __tablename__ = "step_up_challenges"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    methods: Mapped[list[str]] = mapped_column(JSON)
    expires_at: Mapped[int]
    used_at: Mapped[int | None] = mapped_column(nullable=True)
