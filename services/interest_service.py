from typing import List
from sqlalchemy.orm import Session
from repositories.interest_repository import InterestRepository
from schemas.interest_schemas import InterestResponse, InterestsListResponse
from core.i18n import translate


class InterestService:
    """Сервис для работы с интересами"""
    
    def __init__(self, db: Session):
        self._repository = InterestRepository(db)
    
    def get_all_interests(self, lang: str = 'ru') -> InterestsListResponse:
        """Получить все интересы"""
        interests = self._repository.get_all()
        interest_responses = [
            InterestResponse(id=interest.id, name=translate(interest.name, lang)) for interest in interests
        ]
        return InterestsListResponse(interests=interest_responses)
    
    def validate_interest_ids(self, interest_ids: List[int]) -> bool:
        """Проверить что все ID интересов существуют"""
        if not interest_ids:
            return True
        
        existing_interests = self._repository.get_by_ids(interest_ids)
        return len(existing_interests) == len(interest_ids) 