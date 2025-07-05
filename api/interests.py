from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.interest_service import InterestService
from schemas.interest_schemas import InterestsListResponse

router = APIRouter(prefix="/interests", tags=["Interests"])


def get_interest_service(db: Session = Depends(get_db)) -> InterestService:
    return InterestService(db)


@router.get("/", response_model=InterestsListResponse)
async def get_all_interests(
    interest_service: InterestService = Depends(get_interest_service)
):
    """Получить все интересы"""
    return interest_service.get_all_interests() 