from sqlalchemy.orm import Session
from repositories.toy_category_repository import ToyCategoryRepository
from schemas.toy_category_schemas import ToyCategoryResponse, ToyCategoriesListResponse


class ToyCategoryService:
    """Сервис для работы с категориями игрушек"""
    
    def __init__(self, db: Session):
        self._repository = ToyCategoryRepository(db)
    
    def get_all_categories(self) -> ToyCategoriesListResponse:
        """Получить все категории игрушек"""
        categories = self._repository.get_all()
        category_responses = [
            ToyCategoryResponse.model_validate(category) for category in categories
        ]
        return ToyCategoriesListResponse(categories=category_responses) 