from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_admin
from services.category_mapping_service import CategoryMappingService
from repositories.toy_category_repository import ToyCategoryRepository
from repositories.interest_repository import InterestRepository
from repositories.skill_repository import SkillRepository
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin Mappings"])

# Схемы для управления маппингом
class CategoryMappingResponse(BaseModel):
    category_id: int
    category_name: str
    interests: List[str]
    skills: List[str]

class AddMappingRequest(BaseModel):
    interest_id: int = None
    skill_id: int = None

class InterestResponse(BaseModel):
    id: int
    name: str

class SkillResponse(BaseModel):
    id: int
    name: str

@router.get("/interests", response_model=List[InterestResponse])
async def get_all_interests(
    current_admin: dict = Depends(get_current_admin),
    interest_repo: InterestRepository = Depends(lambda db=Depends(get_db): InterestRepository(db))
):
    """Получить все интересы для админки"""
    interests = interest_repo.get_all()
    return [InterestResponse(id=interest.id, name=interest.name) for interest in interests]

@router.get("/skills", response_model=List[SkillResponse])
async def get_all_skills(
    current_admin: dict = Depends(get_current_admin),
    skill_repo: SkillRepository = Depends(lambda db=Depends(get_db): SkillRepository(db))
):
    """Получить все навыки для админки"""
    skills = skill_repo.get_all()
    return [SkillResponse(id=skill.id, name=skill.name) for skill in skills]

@router.get("/category-mappings", response_model=List[CategoryMappingResponse])
async def get_category_mappings(
    current_admin: dict = Depends(get_current_admin),
    mapping_service: CategoryMappingService = Depends(lambda db=Depends(get_db): CategoryMappingService(db))
):
    """Получить все маппинги категорий с интересами и навыками"""
    db = next(get_db())
    category_repo = ToyCategoryRepository(db)
    interest_repo = InterestRepository(db)
    skill_repo = SkillRepository(db)
    
    categories = category_repo.get_all()
    result = []
    
    for category in categories:
        interests = [interest.name for interest in category.interests]
        skills = [skill.name for skill in category.skills]
        
        result.append(CategoryMappingResponse(
            category_id=category.id,
            category_name=category.name,
            interests=interests,
            skills=skills
        ))
    
    return result

@router.post("/category-mappings/{category_id}/interests")
async def add_interest_to_category(
    category_id: int,
    request: AddMappingRequest,
    current_admin: dict = Depends(get_current_admin),
    mapping_service: CategoryMappingService = Depends(lambda db=Depends(get_db): CategoryMappingService(db))
):
    """Добавить интерес к категории"""
    if not request.interest_id:
        raise HTTPException(status_code=400, detail="interest_id обязателен")
    
    success = mapping_service.add_interest_to_category(category_id, request.interest_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось добавить интерес к категории")
    
    return {"message": "Интерес добавлен к категории"}

@router.post("/category-mappings/{category_id}/skills")
async def add_skill_to_category(
    category_id: int,
    request: AddMappingRequest,
    current_admin: dict = Depends(get_current_admin),
    mapping_service: CategoryMappingService = Depends(lambda db=Depends(get_db): CategoryMappingService(db))
):
    """Добавить навык к категории"""
    if not request.skill_id:
        raise HTTPException(status_code=400, detail="skill_id обязателен")
    
    success = mapping_service.add_skill_to_category(category_id, request.skill_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось добавить навык к категории")
    
    return {"message": "Навык добавлен к категории"}

@router.delete("/category-mappings/{category_id}/interests/{interest_id}")
async def remove_interest_from_category(
    category_id: int,
    interest_id: int,
    current_admin: dict = Depends(get_current_admin),
    mapping_service: CategoryMappingService = Depends(lambda db=Depends(get_db): CategoryMappingService(db))
):
    """Удалить интерес из категории"""
    success = mapping_service.remove_interest_from_category(category_id, interest_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось удалить интерес из категории")
    
    return {"message": "Интерес удален из категории"}

@router.delete("/category-mappings/{category_id}/skills/{skill_id}")
async def remove_skill_from_category(
    category_id: int,
    skill_id: int,
    current_admin: dict = Depends(get_current_admin),
    mapping_service: CategoryMappingService = Depends(lambda db=Depends(get_db): CategoryMappingService(db))
):
    """Удалить навык из категории"""
    success = mapping_service.remove_skill_from_category(category_id, skill_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось удалить навык из категории")
    
    return {"message": "Навык удален из категории"} 