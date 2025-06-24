from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services.subscription_service import SubscriptionService
from services.payment_service import MockPaymentService
from pydantic import BaseModel

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


class SubscriptionCreate(BaseModel):
    plan_name: str
    user_id: int


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


def get_payment_service(db: Session = Depends(get_db)) -> MockPaymentService:
    return MockPaymentService(db)


@router.get("/plans")
async def get_subscription_plans(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Получает доступные планы подписки"""
    return subscription_service.get_available_plans()


@router.post("/subscribe")
async def create_subscription(
    subscription_data: SubscriptionCreate,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    payment_service: MockPaymentService = Depends(get_payment_service)
):
    """Создает подписку и инициирует платеж"""
    try:
        # Создаем подписку
        subscription = subscription_service.create_subscription(
            user_id=subscription_data.user_id,
            plan_name=subscription_data.plan_name
        )
        
        # Создаем платеж
        payment_id = payment_service.create_payment(
            user_id=subscription_data.user_id,
            subscription_id=subscription.id,
            amount=subscription.price
        )
        
        return {
            "subscription_id": subscription.id,
            "payment_id": payment_id,
            "amount": subscription.price,
            "message": "Подписка создана, переходите к оплате"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_subscriptions(
    user_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Получает подписки пользователя"""
    subscriptions = subscription_service.get_user_subscriptions(user_id)
    return subscriptions


@router.post("/payment/{payment_id}/process")
async def process_payment(
    payment_id: int,
    payment_service: MockPaymentService = Depends(get_payment_service)
):
    """Обрабатывает платеж"""
    success = payment_service.process_payment(payment_id)
    
    if success:
        return {"status": "success", "message": "Платеж успешно обработан"}
    else:
        return {"status": "failed", "message": "Платеж не прошел"} 