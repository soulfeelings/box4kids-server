from datetime import date as date_type
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from services.delivery_date_exclusion_service import DeliveryDateExclusionService

router = APIRouter(prefix="/admin/delivery-dates", tags=["Admin Delivery Dates"])


class DateResponse(BaseModel):
    dates: List[date_type]


def get_service(db: Session = Depends(get_db)) -> DeliveryDateExclusionService:
    return DeliveryDateExclusionService(db)


@router.get("/", response_model=DateResponse)
async def list_disabled_dates(service: DeliveryDateExclusionService = Depends(get_service)):
    """Получить все запрещённые даты доставки."""
    return DateResponse(dates=service.list_exclusions())


@router.post("/{date_value}")
async def add_disabled_date(date_value: date_type, service: DeliveryDateExclusionService = Depends(get_service)):
    """Добавить дату в список запрещённых."""
    service.add_exclusion(date_value)
    return {"message": "Date disabled"}


@router.delete("/{date_value}")
async def remove_disabled_date(date_value: date_type, service: DeliveryDateExclusionService = Depends(get_service)):
    """Удалить дату из списка запрещённых."""
    success = service.remove_exclusion(date_value)
    if not success:
        raise HTTPException(status_code=404, detail="Date not found")
    return {"message": "Date enabled"}
