from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from services.delivery_info_service import DeliveryInfoService
from schemas.delivery_info_schemas import (
    DeliveryInfoCreate,
    DeliveryInfoUpdate, 
    DeliveryInfoResponse,
    DeliveryInfoListResponse
)
from typing import Optional

router = APIRouter(prefix="/delivery-addresses", tags=["Delivery Addresses"])


def get_delivery_service(db: Session = Depends(get_db)) -> DeliveryInfoService:
    return DeliveryInfoService(db)


@router.get("/", response_model=DeliveryInfoListResponse)
async def get_user_delivery_addresses(
    user_id: int,
    limit: Optional[int] = Query(None, description="Максимальное количество адресов"),
    delivery_service: DeliveryInfoService = Depends(get_delivery_service)
):
    """Получить адреса доставки пользователя"""
    return delivery_service.get_user_addresses(user_id, limit)


@router.post("/", response_model=DeliveryInfoResponse)
async def create_delivery_address(
    user_id: int,
    address_data: DeliveryInfoCreate,
    delivery_service: DeliveryInfoService = Depends(get_delivery_service)
):
    """Создать новый адрес доставки"""
    return delivery_service.create_address(user_id, address_data)


@router.put("/{address_id}", response_model=DeliveryInfoResponse)
async def update_delivery_address(
    address_id: int,
    user_id: int,
    update_data: DeliveryInfoUpdate,
    delivery_service: DeliveryInfoService = Depends(get_delivery_service)
):
    """Обновить адрес доставки"""
    updated_address = delivery_service.update_address(user_id, address_id, update_data)
    if not updated_address:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    return updated_address


@router.delete("/{address_id}")
async def delete_delivery_address(
    address_id: int,
    user_id: int,
    delivery_service: DeliveryInfoService = Depends(get_delivery_service)
):
    """Удалить адрес доставки"""
    success = delivery_service.delete_address(user_id, address_id)
    if not success:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    return {"message": "Адрес успешно удален"} 