from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from services.delivery_info_service import DeliveryInfoService
from schemas.auth_schemas import UserFromToken
from schemas.delivery_info_schemas import (
    DeliveryInfoCreate,
    DeliveryInfoUpdate, 
    DeliveryInfoResponse,
    DeliveryInfoListResponse
)
from typing import Optional
from core.i18n import translate

router = APIRouter(prefix="/delivery-addresses", tags=["Delivery Addresses"])


def get_delivery_service(db: Session = Depends(get_db)) -> DeliveryInfoService:
    return DeliveryInfoService(db)


@router.get("/", response_model=DeliveryInfoListResponse)
async def get_user_delivery_addresses(
    current_user: UserFromToken = Depends(get_current_user),
    limit: Optional[int] = Query(None, description="Максимальное количество адресов"),
    delivery_service: DeliveryInfoService = Depends(get_delivery_service)
):
    """Получить адреса доставки текущего пользователя"""
    return delivery_service.get_user_addresses(current_user.id, limit)


@router.post("/", response_model=DeliveryInfoResponse)
async def create_delivery_address(
    address_data: DeliveryInfoCreate,
    current_user: UserFromToken = Depends(get_current_user),
    delivery_service: DeliveryInfoService = Depends(get_delivery_service)
):
    """Создать новый адрес доставки для текущего пользователя"""
    return delivery_service.create_address(current_user.id, address_data)


@router.put("/{address_id}", response_model=DeliveryInfoResponse)
async def update_delivery_address(
    address_id: int,
    update_data: DeliveryInfoUpdate,
    current_user: UserFromToken = Depends(get_current_user),
    delivery_service: DeliveryInfoService = Depends(get_delivery_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    updated_address = delivery_service.update_address(current_user.id, address_id, update_data)
    if not updated_address:
        raise HTTPException(status_code=404, detail=translate('address_not_found', lang))
    return updated_address


@router.delete("/{address_id}")
async def delete_delivery_address(
    address_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    delivery_service: DeliveryInfoService = Depends(get_delivery_service),
    req: Request = None
):
    lang = req.state.lang if req and hasattr(req.state, 'lang') else 'ru'
    success = delivery_service.delete_address(current_user.id, address_id)
    if not success:
        raise HTTPException(status_code=404, detail=translate('address_not_found', lang))
    return {"message": translate('address_deleted', lang)} 