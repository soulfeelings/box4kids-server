from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class DeliveryInfo(Base):
    __tablename__ = "delivery_info"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # Название адреса (Дом, Работа, и т.д.)
    address = Column(String, nullable=False)  # Полный адрес доставки
    delivery_time_preference = Column(String, nullable=True)  # Предпочтительное время доставки
    courier_comment = Column(Text, nullable=True)  # Комментарий для курьера
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="delivery_addresses") 