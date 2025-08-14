from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.security import get_current_admin
from services.allowed_delivery_date_service import AllowedDeliveryDateService
from schemas.delivery_date_schemas import AllowedDatesResponse, AllowedDateRequest


router = APIRouter(prefix="/admin/delivery-dates", tags=["Admin Delivery Dates"])


@router.get("/", response_model=AllowedDatesResponse)
def list_allowed_dates(
    current_admin: dict = Depends(get_current_admin),
    service: AllowedDeliveryDateService = Depends(lambda db=Depends(get_db): AllowedDeliveryDateService(db)),
):
    dates = service.list_dates()
    return {"dates": [d.isoformat() for d in dates]}


@router.post("/", response_model=AllowedDatesResponse)
def add_allowed_date(
    payload: AllowedDateRequest,
    current_admin: dict = Depends(get_current_admin),
    service: AllowedDeliveryDateService = Depends(lambda db=Depends(get_db): AllowedDeliveryDateService(db)),
):
    try:
        d = date.fromisoformat(payload.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты, ожидается YYYY-MM-DD")
    service.add_date(d)
    dates = service.list_dates()
    return {"dates": [x.isoformat() for x in dates]}


@router.delete("/{target_date}", response_model=AllowedDatesResponse)
def remove_allowed_date(
    target_date: str,
    current_admin: dict = Depends(get_current_admin),
    service: AllowedDeliveryDateService = Depends(lambda db=Depends(get_db): AllowedDeliveryDateService(db)),
):
    try:
        d = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты, ожидается YYYY-MM-DD")
    service.remove_date(d)
    dates = service.list_dates()
    return {"dates": [x.isoformat() for x in dates]}

