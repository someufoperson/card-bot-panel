import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import DATE, NUMERIC, TEXT, UUID, VARCHAR, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    bank: Mapped[str | None] = mapped_column(VARCHAR(100))
    card_number: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, unique=True)
    card_last4: Mapped[str] = mapped_column(VARCHAR(4), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(VARCHAR(20))
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    purchase_date: Mapped[date | None] = mapped_column(DATE)
    pickup_date: Mapped[date | None] = mapped_column(DATE)
    group_name: Mapped[str | None] = mapped_column(VARCHAR(100))
    balance: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False, default=Decimal("0"))
    monthly_turnover: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False, default=Decimal("0"))
    responsible_user: Mapped[str | None] = mapped_column(VARCHAR(200), nullable=True)
    folder_link: Mapped[str | None] = mapped_column(VARCHAR(500), nullable=True)
    comment: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
