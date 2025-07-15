from sqlalchemy.orm import Session
from models.subscription import Subscription
from models.payment import Payment, PaymentStatus
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from core.config import settings


class SubscriptionUpdateFields(BaseModel):
    """Типизированные поля для обновления подписки"""
    child_id: Optional[int] = None
    plan_id: Optional[int] = None
    delivery_info_id: Optional[int] = None
    payment_id: Optional[int] = None
    discount_percent: Optional[float] = None
    individual_price: Optional[float] = None
    expires_at: Optional[datetime] = None
    auto_renewal: Optional[bool] = None


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, subscription: Subscription) -> Subscription:
        """Создает новую подписку"""
        self.db.add(subscription)
        self.db.flush()
        self.db.refresh(subscription)
        return subscription

    def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Получает подписку по ID"""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def get_by_child_id(self, child_id: int) -> List[Subscription]:
        """Получает все подписки ребенка"""
        return self.db.query(Subscription).filter(
            Subscription.child_id == child_id
        ).order_by(Subscription.created_at.desc()).all()
    
    def get_by_payment_id(self, payment_id: int) -> Optional[Subscription]:
        """Получает все подписки привязанные к платежу"""
        return self.db.query(Subscription).filter(
            Subscription.payment_id == payment_id
        ).first()

    def get_active_by_child_id(self, child_id: int) -> Optional[Subscription]:
        """Получает активную подписку ребенка"""
        # Активная подписка = есть payment, payment.status=COMPLETED, expires_at > now
        return self.db.query(Subscription).join(Payment).filter(
            Subscription.child_id == child_id,
            Payment.status == PaymentStatus.COMPLETED,
            Subscription.expires_at > datetime.now(timezone.utc)
        ).first()

    def get_by_user_id(self, user_id: int) -> List[Subscription]:
        """Получает все подписки пользователя (через детей)"""
        return self.db.query(Subscription).join(
            Subscription.child
        ).filter(
            Subscription.child.has(parent_id=user_id)
        ).order_by(Subscription.created_at.desc()).all()

    def get_pending_payment_by_user_id(self, user_id: int) -> List[Subscription]:
        """Получает подписки пользователя ожидающие оплату"""
        return self.db.query(Subscription).join(
            Subscription.child
        ).filter(
            Subscription.child.has(parent_id=user_id),
            Subscription.payment_id.is_(None)  # Не привязаны к платежу
        ).order_by(Subscription.created_at.desc()).all()

    def deactivate_user_subscriptions(self, user_id: int) -> int:
        """Отменяет все платежи пользователя (тем самым деактивируя подписки)"""
        # Находим все активные платежи пользователя
        payment_ids = self.db.query(Payment.id).filter(
            Payment.user_id == user_id,
            Payment.status == PaymentStatus.COMPLETED
        ).all()
        
        if payment_ids:
            ids_list = [payment_id[0] for payment_id in payment_ids]
            updated_count = self.db.query(Payment).filter(
                Payment.id.in_(ids_list)
            ).update({
                "status": PaymentStatus.REFUNDED
            })
            return updated_count
        
        return 0

    def deactivate_child_subscriptions(self, child_id: int) -> int:
        """Отменяет платежи за подписки конкретного ребенка"""
        # Находим все платежи связанные с подписками этого ребенка
        payment_ids = self.db.query(Payment.id).join(
            Subscription, Payment.id == Subscription.payment_id
        ).filter(
            Subscription.child_id == child_id,
            Payment.status == PaymentStatus.COMPLETED
        ).all()
        
        if payment_ids:
            ids_list = [payment_id[0] for payment_id in payment_ids]
            updated_count = self.db.query(Payment).filter(
                Payment.id.in_(ids_list)
            ).update({
                "status": PaymentStatus.REFUNDED
            })
            return updated_count
        
        return 0

    def get_pending_payment_subscriptions(self) -> List[Subscription]:
        """Получает подписки ожидающие оплату"""
        return self.db.query(Subscription).filter(
            Subscription.payment_id.is_(None)
        ).all()

    def get_active_subscriptions(self) -> List[Subscription]:
        """Получает все активные подписки"""
        return self.db.query(Subscription).join(Payment).filter(
            Payment.status == PaymentStatus.COMPLETED,
            Subscription.expires_at > datetime.utcnow()
        ).all()

    def get_expiring_subscriptions(self, days_ahead: Optional[int] = None) -> List[Subscription]:
        """Получает подписки, которые истекают в ближайшие N дней"""
        from datetime import timedelta
        
        if days_ahead is None:
            days_ahead = settings.SUBSCRIPTION_EXPIRING_NOTIFICATION_DAYS
            
        future_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        return self.db.query(Subscription).join(Payment).filter(
            Payment.status == PaymentStatus.COMPLETED,
            Subscription.expires_at <= future_date,
            Subscription.expires_at > datetime.now(timezone.utc)
        ).all()

    def has_non_cancelled_subscription(self, child_id: int) -> bool:
        """Проверяет есть ли у ребенка не отмененная подписка"""
        # Не отмененная = payment_id IS NULL ИЛИ payment.status = COMPLETED
        
        # Проверяем подписки без платежа (ждут оплаты)
        pending_subscription = self.db.query(Subscription).filter(
            Subscription.child_id == child_id,
            Subscription.payment_id.is_(None)
        ).first()
        
        if pending_subscription:
            return True
        
        # Проверяем подписки с успешным платежом (неважно истекли или нет)
        paid_subscription = self.db.query(Subscription).join(Payment).filter(
            Subscription.child_id == child_id,
            Payment.status == PaymentStatus.COMPLETED
        ).first()
        
        return paid_subscription is not None

    def get_child_subscriptions_history(self, child_id: int) -> List[Subscription]:
        """Получает всю историю подписок ребенка (включая отмененные)"""
        return self.db.query(Subscription).filter(
            Subscription.child_id == child_id
        ).order_by(Subscription.created_at.desc()).all()

    def get_pending_payment_by_child_id(self, child_id: int) -> Optional[Subscription]:
        """Получает неоплаченную подписку ребенка"""
        return self.db.query(Subscription).filter(
            Subscription.child_id == child_id,
            Subscription.payment_id.is_(None)
        ).first()

    def update(self, subscription_id: int, update_data: SubscriptionUpdateFields) -> Optional[Subscription]:
        """Универсальный метод для обновления подписки"""
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if not subscription:
            return None
        
        # Обновляем только переданные поля (не None)
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(subscription, field, value)
        
        self.db.flush()
        self.db.refresh(subscription)
        
        return subscription 