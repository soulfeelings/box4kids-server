from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services.subscription_service import SubscriptionService
from services.payment_service import PaymentService
from models.subscription import SubscriptionStatus
from schemas.subscription_schemas import SubscriptionUpdateRequest
from pydantic import BaseModel

router = APIRouter(prefix="/payments", tags=["Payments"])


class PaymentReturnRequest(BaseModel):
    external_payment_id: str
    status: str = "success"  # success или failed


class PaymentWebhookRequest(BaseModel):
    external_payment_id: str
    status: str  # succeeded, failed, refunded, pending


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


@router.post("/{payment_id}/process")
async def process_payment(
    payment_id: int,
    payment_service: PaymentService = Depends(get_payment_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Обрабатывает платеж и активирует подписку (с реалистичной задержкой 5-15 сек)"""
    try:
        # Асинхронно обрабатываем платеж с имитацией времени
        success = await payment_service.process_payment_async(payment_id)
        
        if success:
            # Получаем информацию о платеже
            payment = payment_service.get_payment_by_id(payment_id)
            if payment and payment.subscription_id:
                # Активируем подписку
                update_data = SubscriptionUpdateRequest(status=SubscriptionStatus.ACTIVE)
                subscription_service.update_subscription(payment.subscription_id, update_data)
            
            return {"status": "success", "message": "Платеж успешно обработан, подписка активирована"}
        else:
            return {"status": "failed", "message": "Платеж не прошел"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка обработки платежа")


@router.post("/return")
async def payment_return(
    request: PaymentReturnRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Имитация возврата с платежной страницы"""
    try:
        result = payment_service.handle_user_return(
            request.external_payment_id, 
            request.status
        )
        
        if result.get("status") == "success":
            # Активируем подписку
            payment = payment_service.get_payment_by_id(result["payment_id"])
            if payment and payment.subscription_id:
                update_data = SubscriptionUpdateRequest(status=SubscriptionStatus.ACTIVE)
                subscription_service.update_subscription(payment.subscription_id, update_data)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка обработки возврата")


@router.post("/webhook")
async def payment_webhook(
    request: PaymentWebhookRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Имитация webhook от платежной системы"""
    try:
        success = payment_service.handle_webhook(
            request.external_payment_id,
            request.status
        )
        
        if success and request.status == "succeeded":
            # Активируем подписку
            payment = payment_service.get_payment_by_external_id(request.external_payment_id)
            if payment and payment.subscription_id:
                update_data = SubscriptionUpdateRequest(status=SubscriptionStatus.ACTIVE)
                subscription_service.update_subscription(payment.subscription_id, update_data)
        
        return {"status": "ok" if success else "error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка обработки webhook") 