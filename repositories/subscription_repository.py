from sqlalchemy.orm import Session
from models.subscription import Subscription
from models.payment import Payment, PaymentStatus
from datetime import datetime
from typing import List, Optional


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

    def get_active_by_child_id(self, child_id: int) -> Optional[Subscription]:
        """Получает активную подписку ребенка"""
        # Активная подписка = есть payment, payment.status=COMPLETED, expires_at > now
        return self.db.query(Subscription).join(Payment).filter(
            Subscription.child_id == child_id,
            Payment.status == PaymentStatus.COMPLETED,
            Subscription.expires_at > datetime.utcnow()
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

    def get_expiring_subscriptions(self, days_ahead: int = 3) -> List[Subscription]:
        """Получает подписки истекающие в ближайшие N дней"""
        from datetime import timedelta
        future_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return self.db.query(Subscription).join(Payment).filter(
            Payment.status == PaymentStatus.COMPLETED,
            Subscription.expires_at <= future_date,
            Subscription.expires_at > datetime.utcnow()
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