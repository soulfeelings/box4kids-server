from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.skill_service import SkillService
from schemas.skill_schemas import SkillsListResponse

router = APIRouter(prefix="/skills", tags=["Skills"])


def get_skill_service(db: Session = Depends(get_db)) -> SkillService:
    return SkillService(db)


@router.get("/", response_model=SkillsListResponse)
async def get_all_skills(
    skill_service: SkillService = Depends(get_skill_service)
):
    """Получить все навыки"""
    return skill_service.get_all_skills() 