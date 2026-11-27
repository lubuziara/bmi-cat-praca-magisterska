from sqlalchemy import ForeignKey, String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class Passkey(Base):
    __tablename__ = "passkeys"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    public_key: Mapped[bytes] = mapped_column(LargeBinary)
    sign_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[int]
    last_used_at: Mapped[int | None] = mapped_column(nullable=True)
    name: Mapped[str | None] = mapped_column(String(80), nullable=True)

class PasskeyChallenge(Base):
    __tablename__ = "passkey_challenges"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(16))
    expires_at: Mapped[int]
    used_at: Mapped[int | None] = mapped_column(nullable=True)
