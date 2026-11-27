from datetime import date
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class OwnerProfile(Base):
    __tablename__ = "owner_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    last_name: Mapped[str] = mapped_column(String(80))
    gender: Mapped[str] = mapped_column(String(24))
    birth_date: Mapped[date]
    phone: Mapped[str] = mapped_column(String(16))
    email_verified: Mapped[bool] = mapped_column(default=False)
    phone_verified: Mapped[bool] = mapped_column(default=False)
