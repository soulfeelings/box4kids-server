from sqlalchemy import Column, Integer, Date, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from core.database import Base


class AllowedDeliveryDate(Base):
    __tablename__ = "allowed_delivery_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        UniqueConstraint("date", name="uq_allowed_delivery_date_date"),
    )

