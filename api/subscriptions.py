from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services.subscription_service import SubscriptionService
from services.payment_service import PaymentService
from schemas.subscription_schemas import (
    SubscriptionCreateRequest,
    SubscriptionOrderResponse,
    SubscriptionResponse,
    SubscriptionWithDetailsResponse,
    SubscriptionStatusUpdate,
    SubscriptionListResponse
)
from typing import List

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


@router.post("/create-order", response_model=SubscriptionOrderResponse)
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


@router.patch("/{subscription_id}/status", response_model=SubscriptionResponse)
async def update_subscription_status(
    subscription_id: int,
    status_update: SubscriptionStatusUpdate,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Обновляет статус подписки"""
    subscription = subscription_service.update_subscription_status(
        subscription_id, status_update.status
    )
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    return subscription


@router.post("/{subscription_id}/activate", response_model=SubscriptionResponse)
async def activate_subscription(
    subscription_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Активирует подписку (после успешной оплаты)"""
    subscription = subscription_service.activate_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    return subscription


@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
async def pause_subscription(
    subscription_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Приостанавливает подписку"""
    subscription = subscription_service.pause_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    return subscription


@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
async def resume_subscription(
    subscription_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Возобновляет подписку"""
    subscription = subscription_service.resume_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    return subscription


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Отменяет подписку"""
    subscription = subscription_service.cancel_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    return subscription


@router.post("/payment/{payment_id}/process")
async def process_payment(
    payment_id: int,
    payment_service: PaymentService = Depends(get_payment_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Обрабатывает платеж и активирует подписку"""
    try:
        # Обрабатываем платеж
        success = payment_service.process_payment(payment_id)
        
        if success:
            # Получаем информацию о платеже
            payment = payment_service.get_payment_by_id(payment_id)
            if payment and payment.subscription_id:
                # Активируем подписку
                subscription_service.activate_subscription(payment.subscription_id)
            
            return {"status": "success", "message": "Платеж успешно обработан, подписка активирована"}
        else:
            return {"status": "failed", "message": "Платеж не прошел"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка обработки платежа") 