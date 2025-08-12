from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from services.payment_service import PaymentService
from schemas.auth_schemas import UserFromToken
from schemas.payment_schemas import (
    BatchPaymentCreateRequest,
    BatchPaymentResponse,
    ProcessPaymentResponse,
    PaymentReturnRequest,
    PaymentWebhookRequest,
    ProcessSubscriptionsRequest,
    ProcessSubscriptionsResponse,
)
from core.i18n import translate

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


@router.post("/create-batch", response_model=BatchPaymentResponse)
async def create_batch_payment(
    request: BatchPaymentCreateRequest,
    current_user: UserFromToken = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
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
            message=translate('batch_payment_created', lang)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Ошибка при создании пакетного платежа: {e}")
        raise HTTPException(status_code=500, detail=translate('internal_server_error', lang))


@router.post("/{payment_id}/process", response_model=ProcessPaymentResponse)
async def process_payment(
    payment_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    try:
        # Асинхронно обрабатываем платеж с имитацией времени
        success = await payment_service.process_payment_async(payment_id)
        
        if success:
            # Подписки активируются автоматически через property status
            return ProcessPaymentResponse(status="success", message=translate('payment_success', lang))
        else:
            return ProcessPaymentResponse(status="failed", message=translate('payment_failed', lang))
    except Exception:
        raise HTTPException(status_code=500, detail=translate('payment_processing_error', lang))


@router.post("/process-subscriptions", response_model=ProcessSubscriptionsResponse)
async def process_subscriptions(
    request: ProcessSubscriptionsRequest,
    current_user: UserFromToken = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    try:
        # Создаем платеж и сразу обрабатываем его
        result = await payment_service.create_and_process_payment(request.subscription_ids)
        
        return ProcessSubscriptionsResponse(
            status=result.status,
            message=result.message,
            payment_id=result.payment_id,
            amount=result.amount
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Ошибка при обработке подписок: {e}")
        raise HTTPException(status_code=500, detail=translate('internal_server_error', lang))


@router.post("/return")
async def payment_return(
    request: PaymentReturnRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Имитация возврата с платежной страницы"""
    try:
        result = payment_service.handle_user_return(
            request.external_payment_id, 
            request.status
        )
        
        return result
    except Exception:
        raise HTTPException(status_code=500, detail=translate('payment_return_error', lang))


@router.post("/webhook")
async def payment_webhook(
    request: PaymentWebhookRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    """Имитация webhook от платежной системы"""
    try:
        success = payment_service.handle_webhook(
            request.external_payment_id,
            request.status
        )
        
        return {"status": "ok" if success else "error"}
    except Exception:
        raise HTTPException(status_code=500, detail=translate('webhook_processing_error', lang)) 