from sqlalchemy.orm import Session
from models.subscription import Subscription, SubscriptionStatus
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
        return self.db.query(Subscription).filter(
            Subscription.child_id == child_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).first()

    def get_by_user_id(self, user_id: int) -> List[Subscription]:
        """Получает все подписки пользователя (через детей)"""
        return self.db.query(Subscription).join(
            Subscription.child
        ).filter(
            Subscription.child.has(parent_id=user_id)
        ).order_by(Subscription.created_at.desc()).all()

    def update_status(self, subscription_id: int, status: SubscriptionStatus) -> Optional[Subscription]:
        """Обновляет статус подписки"""
        subscription = self.get_by_id(subscription_id)
        if subscription:
            subscription.status = status
            self.db.flush()
            self.db.refresh(subscription)
        return subscription

    def deactivate_user_subscriptions(self, user_id: int) -> int:
        """Деактивирует все активные подписки пользователя"""
        updated_count = self.db.query(Subscription).join(
            Subscription.child
        ).filter(
            Subscription.child.has(parent_id=user_id),
            Subscription.status == SubscriptionStatus.ACTIVE
        ).update({
            "status": SubscriptionStatus.CANCELLED
        })
        return updated_count

    def get_pending_payment_subscriptions(self) -> List[Subscription]:
        """Получает подписки ожидающие оплату"""
        return self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.PENDING_PAYMENT
        ).all() 