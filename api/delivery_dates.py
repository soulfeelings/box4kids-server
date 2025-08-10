from datetime import date as date_type
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from services.delivery_date_exclusion_service import DeliveryDateExclusionService


class DateResponse(BaseModel):
    dates: List[date_type]


router = APIRouter(prefix="/delivery-dates", tags=["Delivery Dates"])


def get_service(db: Session = Depends(get_db)) -> DeliveryDateExclusionService:
    return DeliveryDateExclusionService(db)


@router.get("/disabled", response_model=DateResponse)
async def list_disabled_dates(service: DeliveryDateExclusionService = Depends(get_service)):
    """Публичный эндпоинт: список дат, которые нельзя выбрать для доставки."""
    return DateResponse(dates=service.list_exclusions())
