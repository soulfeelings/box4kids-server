from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from core.database import Base


class SubscriptionStatus(enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(Integer, ForeignKey("children.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    delivery_info_id: Mapped[int] = mapped_column(Integer, ForeignKey("delivery_info.id"), nullable=True)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING_PAYMENT)
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    child = relationship("Child", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan")
    delivery_info = relationship("DeliveryInfo")
    payments = relationship("Payment", back_populates="subscription")
    
    @property
    def user(self):
        """Получает пользователя через связь с ребенком"""
        return self.child.parent 