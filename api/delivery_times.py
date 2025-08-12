from fastapi import APIRouter, Depends
from core.database import get_db
from services.allowed_delivery_time_service import AllowedDeliveryTimeService
from schemas.delivery_time_schemas import AllowedTimesResponse


router = APIRouter(prefix="/delivery-times", tags=["Delivery Times"])


def split_times(values: list[str]) -> tuple[list[str], list[str]]:
    ranges: list[str] = []
    hours: list[str] = []
    for v in values:
        if any(sep in v for sep in ("-", "–", "—")):
            ranges.append(v)
        else:
            hours.append(v)
    return ranges, hours


@router.get("/available", response_model=AllowedTimesResponse)
def get_available_delivery_times(
    service: AllowedDeliveryTimeService = Depends(lambda db=Depends(get_db): AllowedDeliveryTimeService(db)),
):
    times = service.list_times()
    ranges, hours = split_times(times)
    return {"ranges": ranges, "hours": hours}


