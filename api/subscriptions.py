from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from services.subscription_service import SubscriptionService
from schemas.auth_schemas import UserFromToken
from schemas.subscription_schemas import (
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
    SubscriptionResponse,
    SubscriptionWithDetailsResponse,
)
from typing import List

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription_order(
    request: SubscriptionCreateRequest,
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Создает заказ подписки для текущего пользователя"""
    # TODO: Здесь нужно проверить что child_id принадлежит current_user
    # Пока оставляю как есть, но нужно добавить проверку
    try:
        return subscription_service.create_subscription_order(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Ошибка при создании заказа подписки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/user", response_model=List[SubscriptionWithDetailsResponse])
async def get_user_subscriptions(
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Получает подписки текущего пользователя"""
    try:
        subscriptions = subscription_service.get_user_subscriptions(current_user.id)
        return subscriptions
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка получения подписок")


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Получает подписку по ID"""
    subscription = subscription_service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    
    # TODO: Проверить что подписка принадлежит текущему пользователю
    # if subscription.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Нет доступа к этой подписке")
    
    return subscription

@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdateRequest,
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Обновляет подписку"""
    # TODO: Проверить что подписка принадлежит текущему пользователю
    try:
        subscription = subscription_service.update_subscription(subscription_id, update_data)
        if not subscription:
            raise HTTPException(status_code=404, detail="Подписка не найдена")
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Ошибка при обновлении подписки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
 