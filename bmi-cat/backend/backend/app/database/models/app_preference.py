from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class AppPreference(Base):
    __tablename__ = 'app_preferences'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    notifications: Mapped[bool] = mapped_column(default=True)
    target_kcal: Mapped[float] = mapped_column(default=200.0)
