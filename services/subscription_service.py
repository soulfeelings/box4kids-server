from sqlalchemy.orm import Session
from repositories.subscription_repository import SubscriptionRepository, SubscriptionUpdateFields
from repositories.child_repository import ChildRepository
from repositories.subscription_plan_repository import SubscriptionPlanRepository
from repositories.delivery_info_repository import DeliveryInfoRepository
from models.subscription import Subscription
from services.payment_service import PaymentService
from schemas.subscription_schemas import SubscriptionCreateRequest, SubscriptionResponse, SubscriptionUpdateRequest, SubscriptionWithDetailsResponse
from dateutil.relativedelta import relativedelta
from typing import List, Optional
from datetime import datetime, timezone


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.subscription_repo = SubscriptionRepository(db)
        self.child_repo = ChildRepository(db)
        self.plan_repo = SubscriptionPlanRepository(db)
        self.delivery_repo = DeliveryInfoRepository(db)
        self.payment_service = PaymentService(db)

    def create_subscription_order(self, request: SubscriptionCreateRequest) -> SubscriptionResponse:
        """Создает заказ подписки (без платежа, только подписка)"""
        
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

        # Проверяем что у ребенка нет активной (оплаченной) подписки
        active_subscription = self.subscription_repo.get_active_by_child_id(child.id)
        if active_subscription:
            raise ValueError(f"У ребенка уже есть активная подписка. Отмените текущую или дождитесь её истечения.")

        # Проверяем есть ли неоплаченная подписка
        pending_subscription = self.subscription_repo.get_pending_payment_by_child_id(child.id)
        
        if pending_subscription:
            # Если есть неоплаченная подписка, обновляем её план
            update_data = SubscriptionUpdateFields(
                plan_id=request.plan_id,
                individual_price=plan.price_monthly,
                delivery_info_id=request.delivery_info_id
            )
            
            updated_subscription = self.subscription_repo.update(
                pending_subscription.id, 
                update_data
            )
            
            if updated_subscription:
                return SubscriptionResponse(
                    id=updated_subscription.id,
                    child_id=updated_subscription.child_id,
                    plan_id=updated_subscription.plan_id,
                    delivery_info_id=updated_subscription.delivery_info_id,
                    status=updated_subscription.status,
                    discount_percent=updated_subscription.discount_percent,
                    created_at=updated_subscription.created_at,
                    expires_at=updated_subscription.expires_at
                )

        # Рассчитываем скидку
        discount_percent = self._calculate_discount(child.parent_id)
        
        # Создаем подписку БЕЗ status (он будет вычисляться)
        subscription = Subscription(
            child_id=request.child_id,
            plan_id=request.plan_id,
            delivery_info_id=request.delivery_info_id,
            discount_percent=discount_percent,
            individual_price=plan.price_monthly,
            expires_at=datetime.now(timezone.utc) + relativedelta(months=1)
        )
        
        subscription = self.subscription_repo.create(subscription)
        
        return SubscriptionResponse(
            id=subscription.id,
            child_id=subscription.child_id,
            plan_id=subscription.plan_id,
            delivery_info_id=subscription.delivery_info_id,
            status=subscription.status,
            discount_percent=subscription.discount_percent,
            created_at=subscription.created_at,
            expires_at=subscription.expires_at
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

    def cancel_child_subscription(self, child_id: int) -> bool:
        """Отменяет активную подписку ребенка (через отмену платежа)"""
        active_subscription = self.subscription_repo.get_active_by_child_id(child_id)
        if not active_subscription:
            raise ValueError(f"У ребенка нет активной подписки для отмены")
        
        if active_subscription.payment_id:
            # Отменяем платеж (это автоматически деактивирует подписку)
            return self.payment_service.refund_payment(active_subscription.payment_id)
        
        return False

    def get_active_child_subscription(self, child_id: int) -> Optional[Subscription]:
        """Получает активную подписку ребенка"""
        return self.subscription_repo.get_active_by_child_id(child_id)

    def can_create_subscription_for_child(self, child_id: int) -> bool:
        """Проверяет можно ли создать подписку для ребенка"""
        return not self.subscription_repo.has_non_cancelled_subscription(child_id)

    def update_subscription(self, subscription_id: int, update_data: SubscriptionUpdateRequest) -> Optional[Subscription]:
        """Обновляет подписку с валидацией прав доступа"""
        subscription = self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            return None
        
        # Валидация данных ПЕРЕД обновлением
        if update_data.child_id is not None:
            child = self.child_repo.get_by_id(update_data.child_id)
            if not child:
                raise ValueError(f"Ребенок с ID {update_data.child_id} не найден")
            # Проверяем, что ребенок принадлежит тому же пользователю
            if child.parent_id != subscription.user.id:
                raise ValueError("Ребенок не принадлежит владельцу подписки")
        
        if update_data.plan_id is not None:
            plan = self.plan_repo.get_by_id(update_data.plan_id)
            if not plan:
                raise ValueError(f"План с ID {update_data.plan_id} не найден")
        
        if update_data.delivery_info_id is not None:
            delivery_info = self.delivery_repo.get_by_id(update_data.delivery_info_id)
            if not delivery_info:
                raise ValueError(f"Адрес доставки с ID {update_data.delivery_info_id} не найден")
            # Проверяем, что адрес принадлежит пользователю
            if delivery_info.user_id != subscription.user.id:
                raise ValueError("Адрес доставки не принадлежит пользователю")
        
        # Обновляем только переданные поля (кроме status - он вычисляется)
        update_dict = update_data.model_dump(exclude_unset=True)
        if 'status' in update_dict:
            del update_dict['status']  # Убираем status из обновления
        
        # Создаем объект для обновления
        update_fields = SubscriptionUpdateFields(**update_dict)
        
        # Используем универсальный метод репозитория
        return self.subscription_repo.update(subscription_id, update_fields)

    def get_pending_subscriptions_for_user(self, user_id: int) -> List[Subscription]:
        """Получает подписки пользователя ожидающие оплату"""
        return self.subscription_repo.get_pending_payment_by_user_id(user_id)

    def get_child_subscription_history(self, child_id: int) -> List[Subscription]:
        """Получает всю историю подписок ребенка"""
        return self.subscription_repo.get_child_subscriptions_history(child_id) 