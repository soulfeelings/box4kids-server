from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from services.click_payment_service import ClickPaymentService
from schemas.auth_schemas import UserFromToken
from schemas.click_payment_schemas import (
    CreateCardTokenRequest,
    CreateCardTokenResponse,
    VerifyCardTokenRequest,
    VerifyCardTokenResponse,
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    PaymentStatusResponse,
    UserCardTokenResponse
)
from typing import List

router = APIRouter(prefix="/click", tags=["Click Payments"])


@router.post("/card-token/create", response_model=CreateCardTokenResponse)
async def create_card_token(
    request: CreateCardTokenRequest,
    current_user: UserFromToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать токен карты"""
    service = ClickPaymentService(db)
    result = await service.create_card_token(
        current_user.id,
        request.card_number,
        request.expire_date
    )
    return result


@router.post("/card-token/verify", response_model=VerifyCardTokenResponse)
async def verify_card_token(
    request: VerifyCardTokenRequest,
    current_user: UserFromToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Верифицировать токен карты SMS кодом"""
    service = ClickPaymentService(db)
    result = await service.verify_card_token(request.card_token_id, request.sms_code)
    return result


@router.get("/card-tokens", response_model=List[UserCardTokenResponse])
async def get_user_card_tokens(
    current_user: UserFromToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить список токенов карт пользователя"""
    service = ClickPaymentService(db)
    tokens = service.get_user_card_tokens(current_user.id)
    return tokens


@router.post("/payment/initiate", response_model=InitiatePaymentResponse)
async def initiate_payment(
    request: InitiatePaymentRequest,
    current_user: UserFromToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Инициировать платеж по подпискам"""
    service = ClickPaymentService(db)
    result = await service.initiate_payment(
        current_user.id,
        request.subscription_ids,
        request.card_token_id
    )
    return result


@router.get("/payment/status/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статус платежа"""
    service = ClickPaymentService(db)
    result = service.get_payment_status(payment_id, current_user.id)

    if not result:
        raise HTTPException(status_code=404, detail="Платеж не найден")

    return result
