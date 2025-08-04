from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from core.database import get_db
from services.toy_category_service import ToyCategoryService
from schemas.toy_category_schemas import ToyCategoriesListResponse

router = APIRouter(prefix="/toy-categories", tags=["Toy Categories"])


def get_toy_category_service(db: Session = Depends(get_db)) -> ToyCategoryService:
    return ToyCategoryService(db)


@router.get("/", response_model=ToyCategoriesListResponse)
async def get_all_toy_categories(
    request: Request,
    toy_category_service: ToyCategoryService = Depends(get_toy_category_service)
):
    """Получить все категории игрушек"""
    lang = request.state.lang if hasattr(request.state, 'lang') else 'ru'
    return toy_category_service.get_all_categories(lang) 