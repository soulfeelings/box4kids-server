from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from services.payment_service import PaymentService
from schemas.auth_schemas import UserFromToken
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/payments", tags=["Payments"])


class PaymentReturnRequest(BaseModel):
    external_payment_id: str
    status: str = "success"  # success или failed


class PaymentWebhookRequest(BaseModel):
    external_payment_id: str
    status: str  # succeeded, failed, refunded, pending


class BatchPaymentCreateRequest(BaseModel):
    subscription_ids: List[int]


class BatchPaymentResponse(BaseModel):
    payment_id: int
    external_payment_id: str
    payment_url: str
    amount: float
    currency: str
    subscription_count: int
    message: str

def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


@router.post("/create-batch", response_model=BatchPaymentResponse)
async def create_batch_payment(
    request: BatchPaymentCreateRequest,
    current_user: UserFromToken = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Создает пакетный платеж для нескольких подписок"""
    try:
        # Создаем пакетный платеж
        payment_response = payment_service.create_batch_payment(request.subscription_ids)
        
        return BatchPaymentResponse(
            payment_id=payment_response["payment_id"],
            external_payment_id=payment_response["external_payment_id"],
            payment_url=payment_response["payment_url"],
            amount=payment_response["amount"],
            currency=payment_response["currency"],
            subscription_count=len(request.subscription_ids),
            message="Пакетный платеж создан, переходите к оплате"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Ошибка при создании пакетного платежа: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/{payment_id}/process")
async def process_payment(
    payment_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Обрабатывает платеж и активирует подписки (с реалистичной задержкой 5-15 сек)"""
    try:
        # Асинхронно обрабатываем платеж с имитацией времени
        success = await payment_service.process_payment_async(payment_id)
        
        if success:
            # Подписки активируются автоматически через property status
            return {"status": "success", "message": "Платеж успешно обработан, подписки активированы"}
        else:
            return {"status": "failed", "message": "Платеж не прошел"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка обработки платежа")


@router.post("/return")
async def payment_return(
    request: PaymentReturnRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Имитация возврата с платежной страницы"""
    try:
        result = payment_service.handle_user_return(
            request.external_payment_id, 
            request.status
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка обработки возврата")


@router.post("/webhook")
async def payment_webhook(
    request: PaymentWebhookRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Имитация webhook от платежной системы"""
    try:
        success = payment_service.handle_webhook(
            request.external_payment_id,
            request.status
        )
        
        return {"status": "ok" if success else "error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка обработки webhook") 