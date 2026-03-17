import uuid
from datetime import datetime, timezone

from sqlalchemy import VARCHAR, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    serial: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(VARCHAR(200), nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(10), default="offline", nullable=False)
    # Admin grants access before anyone can connect
    session_status: Mapped[str] = mapped_column(VARCHAR(10), default="inactive", nullable=False)
    # True while a scrcpy session is actively running
    connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
