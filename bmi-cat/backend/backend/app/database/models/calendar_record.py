from datetime import date
from sqlalchemy import ForeignKey, String, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class CalendarRecord(Base):
    __tablename__ = 'calendar_records'
    __table_args__ = (UniqueConstraint('cat_id', 'source_key'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    cat_id: Mapped[int] = mapped_column(ForeignKey('cats.id'), index=True)
    source_key: Mapped[str] = mapped_column(String(100))
    day: Mapped[date] = mapped_column(index=True)
    occurred_at: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(120))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
