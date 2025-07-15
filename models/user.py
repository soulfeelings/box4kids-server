from sqlalchemy import String, DateTime, Enum, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from typing import Optional, List, TYPE_CHECKING
from core.database import Base

if TYPE_CHECKING:
    from .child import Child
    from .delivery_info import DeliveryInfo
    from .payment import Payment


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    children: Mapped[List["Child"]] = relationship("Child", back_populates="parent")
    delivery_addresses: Mapped[List["DeliveryInfo"]] = relationship("DeliveryInfo", back_populates="user")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="user") 