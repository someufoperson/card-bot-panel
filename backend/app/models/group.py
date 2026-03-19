from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    type: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)  # 'donor' | 'issuance'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
