import uuid
from datetime import datetime, timezone

from sqlalchemy import TEXT, VARCHAR, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DeviceLog(Base):
    __tablename__ = "device_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    serial: Mapped[str] = mapped_column(VARCHAR(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    detail: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
