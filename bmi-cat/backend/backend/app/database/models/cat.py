from datetime import date
from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Cat(Base):
    __tablename__ = "cats"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    gender: Mapped[str] = mapped_column(String(16))
    birth_date: Mapped[date | None]
    estimated_age_months: Mapped[int | None]
    age_recorded_on: Mapped[date]
    avatar: Mapped[dict] = mapped_column(JSON)
