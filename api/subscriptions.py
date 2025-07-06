from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services.subscription_service import SubscriptionService
from schemas.subscription_schemas import (
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
    SubscriptionCreateResponse,
    SubscriptionResponse,
    SubscriptionWithDetailsResponse,
)
from typing import List

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


@router.post("/", response_model=SubscriptionCreateResponse)
async def create_subscription_order(
    request: SubscriptionCreateRequest,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Создает заказ подписки"""
    try:
        return subscription_service.create_subscription_order(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Ошибка при создании заказа подписки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/user/{user_id}", response_model=List[SubscriptionWithDetailsResponse])
async def get_user_subscriptions(
    user_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Получает подписки пользователя"""
    try:
        subscriptions = subscription_service.get_user_subscriptions(user_id)
        return subscriptions
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка получения подписок")


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Получает подписку по ID"""
    subscription = subscription_service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    return subscription

@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdateRequest,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Обновляет подписку"""
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
 