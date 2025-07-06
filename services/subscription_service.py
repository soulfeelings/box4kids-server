from sqlalchemy.orm import Session
from repositories.subscription_repository import SubscriptionRepository
from repositories.child_repository import ChildRepository
from repositories.subscription_plan_repository import SubscriptionPlanRepository
from repositories.delivery_info_repository import DeliveryInfoRepository
from services.payment_service import PaymentService
from models.subscription import Subscription, SubscriptionStatus
from schemas.subscription_schemas import SubscriptionCreateRequest, SubscriptionOrderResponse, SubscriptionWithDetailsResponse
from typing import List, Optional
from datetime import datetime, timedelta


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.subscription_repo = SubscriptionRepository(db)
        self.child_repo = ChildRepository(db)
        self.plan_repo = SubscriptionPlanRepository(db)
        self.delivery_repo = DeliveryInfoRepository(db)
        self.payment_service = PaymentService(db)

    def create_subscription_order(self, request: SubscriptionCreateRequest) -> SubscriptionOrderResponse:
        """Создает заказ подписки и инициирует платеж"""
        
        # Валидация данных
        child = self.child_repo.get_by_id(request.child_id)
        if not child:
            raise ValueError(f"Ребенок с ID {request.child_id} не найден")
        
        plan = self.plan_repo.get_by_id(request.plan_id)
        if not plan:
            raise ValueError(f"План с ID {request.plan_id} не найден")
        
        if request.delivery_info_id:
            delivery_info = self.delivery_repo.get_by_id(request.delivery_info_id)
            if not delivery_info:
                raise ValueError(f"Адрес доставки с ID {request.delivery_info_id} не найден")
            
            # Проверяем что адрес принадлежит пользователю
            if delivery_info.user_id != child.parent_id:
                raise ValueError("Адрес доставки не принадлежит пользователю")

        # Деактивируем старые подписки ребенка
        self.subscription_repo.deactivate_user_subscriptions(child.parent_id)

        # Рассчитываем скидку
        discount_percent = self._calculate_discount(child.parent_id)
        
        # Создаем подписку
        subscription = Subscription(
            child_id=request.child_id,
            plan_id=request.plan_id,
            delivery_info_id=request.delivery_info_id,
            status=SubscriptionStatus.PENDING_PAYMENT,
            discount_percent=discount_percent,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        subscription = self.subscription_repo.create(subscription)
        
        # Рассчитываем итоговую стоимость
        amount = plan.price_monthly
        final_amount = amount * (1 - discount_percent / 100)
        
        # Создаем платеж
        payment_response = self.payment_service.create_payment(
            user_id=child.parent_id,
            subscription_id=subscription.id,
            amount=final_amount
        )
        
        return SubscriptionOrderResponse(
            subscription_id=subscription.id,
            payment_id=payment_response["payment_id"],
            status=subscription.status,
            amount=amount,
            discount_percent=discount_percent,
            final_amount=final_amount,
            message="Заказ успешно создан, переходите к оплате"
        )

    def _calculate_discount(self, user_id: int) -> float:
        """Рассчитывает скидку для пользователя"""
        # Получаем количество детей у пользователя
        children_count = len(self.child_repo.get_by_parent_id(user_id))
        
        # Скидка 20% для второго ребенка и далее
        if children_count >= 2:
            return 20.0
        
        return 0.0

    def get_user_subscriptions(self, user_id: int) -> List[SubscriptionWithDetailsResponse]:
        """Получает подписки пользователя с подробными данными"""
        subscriptions = self.subscription_repo.get_by_user_id(user_id)
        
        result = []
        for subscription in subscriptions:
            subscription_data = SubscriptionWithDetailsResponse(
                id=subscription.id,
                child_id=subscription.child_id,
                plan_id=subscription.plan_id,
                delivery_info_id=subscription.delivery_info_id,
                status=subscription.status,
                discount_percent=subscription.discount_percent,
                created_at=subscription.created_at,
                expires_at=subscription.expires_at,
                child_name=subscription.child.name,
                plan_name=subscription.plan.name,
                plan_price=subscription.plan.price_monthly,
                user_id=subscription.user.id,
                user_name=subscription.user.name
            )
            result.append(subscription_data)
        
        return result

    def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Получает подписку по ID"""
        return self.subscription_repo.get_by_id(subscription_id)

    def update_subscription_status(self, subscription_id: int, status: SubscriptionStatus) -> Optional[Subscription]:
        """Обновляет статус подписки"""
        return self.subscription_repo.update_status(subscription_id, status)

    def activate_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Активирует подписку (вызывается после успешной оплаты)"""
        return self.update_subscription_status(subscription_id, SubscriptionStatus.ACTIVE)

    def pause_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Приостанавливает подписку"""
        return self.update_subscription_status(subscription_id, SubscriptionStatus.PAUSED)

    def resume_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Возобновляет подписку"""
        return self.update_subscription_status(subscription_id, SubscriptionStatus.ACTIVE)

    def cancel_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Отменяет подписку"""
        return self.update_subscription_status(subscription_id, SubscriptionStatus.CANCELLED) 