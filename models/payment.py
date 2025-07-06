from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from core.database import Base


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="RUB")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"))
    external_payment_id: Mapped[str] = mapped_column(String, nullable=True)  # ID из внешнего сервиса
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments") 