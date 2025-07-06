from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
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
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    delivery_info_id = Column(Integer, ForeignKey("delivery_info.id"), nullable=True)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING_PAYMENT)
    discount_percent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    child = relationship("Child", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan")
    delivery_info = relationship("DeliveryInfo")
    payments = relationship("Payment", back_populates="subscription")
    
    @property
    def user(self):
        """Получает пользователя через связь с ребенком"""
        return self.child.parent 