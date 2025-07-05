from typing import List
from sqlalchemy.orm import Session
from repositories.skill_repository import SkillRepository
from schemas.skill_schemas import SkillResponse, SkillsListResponse


class SkillService:
    """Сервис для работы с навыками"""
    
    def __init__(self, db: Session):
        self._repository = SkillRepository(db)
    
    def get_all_skills(self) -> SkillsListResponse:
        """Получить все навыки"""
        skills = self._repository.get_all()
        skill_responses = [
            SkillResponse.model_validate(skill) for skill in skills
        ]
        return SkillsListResponse(skills=skill_responses)
    
    def validate_skill_ids(self, skill_ids: List[int]) -> bool:
        """Проверить что все ID навыков существуют"""
        if not skill_ids:
            return True
        
        existing_skills = self._repository.get_by_ids(skill_ids)
        return len(existing_skills) == len(skill_ids) 