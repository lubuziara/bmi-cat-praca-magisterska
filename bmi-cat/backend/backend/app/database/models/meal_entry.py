from datetime import date
from sqlalchemy import ForeignKey, String, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class MealEntry(Base):
    __tablename__ = 'meal_entries'
    __table_args__ = (Index('ix_meal_cat_date', 'cat_id', 'day'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    cat_id: Mapped[int] = mapped_column(ForeignKey('cats.id'))
    day: Mapped[date]
    period: Mapped[str] = mapped_column(String(16))
    food_id: Mapped[str] = mapped_column(String(80))
    grams: Mapped[float] = mapped_column(Float)
