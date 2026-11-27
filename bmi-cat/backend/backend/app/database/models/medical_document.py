from sqlalchemy import ForeignKey, String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class MedicalDocument(Base):
    __tablename__ = 'medical_documents'
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(primary_key=True)
    cat_id: Mapped[int] = mapped_column(ForeignKey('cats.id'), index=True)
    title: Mapped[str] = mapped_column(String(120))
    occurred_at: Mapped[str] = mapped_column(String(40))
    preview: Mapped[bytes] = mapped_column(LargeBinary)
    pdf: Mapped[bytes] = mapped_column(LargeBinary)
