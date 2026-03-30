import uuid
from datetime import datetime, timezone

from sqlalchemy import BOOLEAN, TEXT, VARCHAR, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(VARCHAR(100), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    role: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, default="user")
    must_set_password: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
