from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.allowed_delivery_date_service import AllowedDeliveryDateService
from schemas.delivery_date_schemas import AllowedDatesResponse


router = APIRouter(prefix="/delivery-dates", tags=["Delivery Dates"])


@router.get("/available", response_model=AllowedDatesResponse)
def get_available_delivery_dates(
    service: AllowedDeliveryDateService = Depends(lambda db=Depends(get_db): AllowedDeliveryDateService(db)),
):
    dates = service.list_dates()
    return {"dates": [d.isoformat() for d in dates]}

