from sqlalchemy import Integer, String, ForeignKey, Text, DateTime, Date, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date as date_type
from core.database import Base


class DeliveryInfo(Base):
    __tablename__ = "delivery_info"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)  # Название адреса (Дом, Работа, и т.д.)
    address: Mapped[str] = mapped_column(String, nullable=False)  # Полный адрес доставки
    date: Mapped[date_type] = mapped_column(Date, nullable=False)  # Дата доставки
    time: Mapped[str] = mapped_column(String, nullable=False)  # Предпочтительное время доставки
    courier_comment: Mapped[str] = mapped_column(Text, nullable=True)  # Комментарий для курьера
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="delivery_addresses") 