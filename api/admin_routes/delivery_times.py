from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.security import get_current_admin
from services.allowed_delivery_time_service import AllowedDeliveryTimeService
from schemas.delivery_time_schemas import (
    AllowedTimesResponse,
    AddRangeRequest,
    AddHourRequest,
)


router = APIRouter(prefix="/admin/delivery-times", tags=["Admin Delivery Times"])


def split_times(values: list[str]) -> tuple[list[str], list[str]]:
    ranges: list[str] = []
    hours: list[str] = []
    for v in values:
        if any(sep in v for sep in ("-", "–", "—")):
            ranges.append(v)
        else:
            hours.append(v)
    return ranges, hours


@router.get("/", response_model=AllowedTimesResponse)
def list_allowed_times(
    current_admin: dict = Depends(get_current_admin),
    service: AllowedDeliveryTimeService = Depends(lambda db=Depends(get_db): AllowedDeliveryTimeService(db)),
):
    times = service.list_times()
    ranges, hours = split_times(times)
    return {"ranges": ranges, "hours": hours}


@router.post("/range", response_model=AllowedTimesResponse)
def add_allowed_range(
    payload: AddRangeRequest,
    current_admin: dict = Depends(get_current_admin),
    service: AllowedDeliveryTimeService = Depends(lambda db=Depends(get_db): AllowedDeliveryTimeService(db)),
):
    value = payload.range.strip()
    if not value:
        raise HTTPException(status_code=400, detail="Пустой интервал")
    service.add_time(value)
    times = service.list_times()
    ranges, hours = split_times(times)
    return {"ranges": ranges, "hours": hours}


@router.delete("/range/{value}", response_model=AllowedTimesResponse)
def remove_allowed_range(
    value: str,
    current_admin: dict = Depends(get_current_admin),
    service: AllowedDeliveryTimeService = Depends(lambda db=Depends(get_db): AllowedDeliveryTimeService(db)),
):
    service.remove_time(value)
    times = service.list_times()
    ranges, hours = split_times(times)
    return {"ranges": ranges, "hours": hours}


@router.post("/hour", response_model=AllowedTimesResponse)
def add_allowed_hour(
    payload: AddHourRequest,
    current_admin: dict = Depends(get_current_admin),
    service: AllowedDeliveryTimeService = Depends(lambda db=Depends(get_db): AllowedDeliveryTimeService(db)),
):
    value = payload.hour.strip()
    if not value:
        raise HTTPException(status_code=400, detail="Пустой час")
    service.add_time(value)
    times = service.list_times()
    ranges, hours = split_times(times)
    return {"ranges": ranges, "hours": hours}


@router.delete("/hour/{value}", response_model=AllowedTimesResponse)
def remove_allowed_hour(
    value: str,
    current_admin: dict = Depends(get_current_admin),
    service: AllowedDeliveryTimeService = Depends(lambda db=Depends(get_db): AllowedDeliveryTimeService(db)),
):
    service.remove_time(value)
    times = service.list_times()
    ranges, hours = split_times(times)
    return {"ranges": ranges, "hours": hours}


