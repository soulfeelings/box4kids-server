from sqlalchemy import Integer, String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from core.database import Base


class AllowedDeliveryTime(Base):
    __tablename__ = "allowed_delivery_times"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    time: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        UniqueConstraint("time", name="uq_allowed_delivery_time_time"),
    )


