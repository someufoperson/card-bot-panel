import uuid
from datetime import date, datetime, timezone

from sqlalchemy import DATE, VARCHAR, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    bank: Mapped[str | None] = mapped_column(VARCHAR(100))
    card_number: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    card_last4: Mapped[str] = mapped_column(VARCHAR(4), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(VARCHAR(20))
    purchase_date: Mapped[date | None] = mapped_column(DATE)
    group_name: Mapped[str | None] = mapped_column(VARCHAR(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
