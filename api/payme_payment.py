from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from services.payme_payment_service import PaymePaymentService
from schemas.auth_schemas import UserFromToken
from schemas.payme_payment_schemas import (
    SaveCardTokenRequest,
    SaveCardTokenResponse,
    ChargeRequest,
    ChargeResponse
)

router = APIRouter(prefix="/payme", tags=["Payme Payments"])


@router.post("/card-token/save", response_model=SaveCardTokenResponse)
async def save_card_token(
    request: SaveCardTokenRequest,
    current_user: UserFromToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Сохранить токен карты после верификации на фронте"""
    service = PaymePaymentService(db)
    result = await service.save_card_token(current_user.id, request.token)
    return result


@router.post("/charge", response_model=ChargeResponse)
async def charge_subscription(
    request: ChargeRequest,
    current_user: UserFromToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Списать деньги за подписки по сохраненному токену"""
    service = PaymePaymentService(db)
    result = await service.charge_subscription(
        current_user.id,
        request.subscription_ids,
        request.description
    )
    return result
