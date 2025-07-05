from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.toy_category_service import ToyCategoryService
from schemas.toy_category_schemas import ToyCategoriesListResponse

router = APIRouter(prefix="/toy-categories", tags=["Toy Categories"])


def get_toy_category_service(db: Session = Depends(get_db)) -> ToyCategoryService:
    return ToyCategoryService(db)


@router.get("/", response_model=ToyCategoriesListResponse)
async def get_all_toy_categories(
    toy_category_service: ToyCategoryService = Depends(get_toy_category_service)
):
    """Получить все категории игрушек"""
    return toy_category_service.get_all_categories() 