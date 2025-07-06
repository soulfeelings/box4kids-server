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
    payment_id: Mapped[int] = mapped_column(Integer, ForeignKey("payments.id"), nullable=True)
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0)
    individual_price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    auto_renewal: Mapped[bool] = mapped_column(default=False)
    
    # Relationships
    child = relationship("Child", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan")
    delivery_info = relationship("DeliveryInfo")
    payment = relationship("Payment", back_populates="subscriptions")
    
    @property
    def user(self):
        """Получает пользователя через связь с ребенком"""
        return self.child.parent
    
    @property
    def is_active(self) -> bool:
        """Проверяет активна ли подписка"""
        if not self.payment:
            return False
        return (
            self.payment.status.value == "completed" and 
            self.expires_at and
            self.expires_at > datetime.utcnow()
        )
    
    @property
    def status(self) -> SubscriptionStatus:
        """Определяет статус подписки на основе платежа и времени"""
        if not self.payment:
            return SubscriptionStatus.PENDING_PAYMENT
        
        if self.payment.status.value == "pending":
            return SubscriptionStatus.PENDING_PAYMENT
        elif self.payment.status.value == "failed":
            return SubscriptionStatus.CANCELLED
        elif self.payment.status.value == "completed":
            if self.expires_at and self.expires_at <= datetime.utcnow():
                return SubscriptionStatus.EXPIRED
            else:
                return SubscriptionStatus.ACTIVE
        elif self.payment.status.value == "refunded":
            return SubscriptionStatus.CANCELLED
        else:
            return SubscriptionStatus.PENDING_PAYMENT 