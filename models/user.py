from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from core.database import Base


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    children = relationship("Child", back_populates="parent")
    subscriptions = relationship("Subscription", back_populates="user")
    delivery_addresses = relationship("DeliveryInfo", back_populates="user")
    payments = relationship("Payment", back_populates="user") 