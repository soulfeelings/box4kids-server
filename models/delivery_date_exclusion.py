from sqlalchemy import Column, Date, DateTime, Integer, UniqueConstraint, func

from core.database import Base


class DeliveryDateExclusion(Base):
    """Даты, недоступные для выбора доставки пользователями."""

    __tablename__ = "delivery_date_exclusions"
    __table_args__ = (
        UniqueConstraint("date", name="uq_delivery_date_exclusions_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
