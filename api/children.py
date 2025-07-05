from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services.child_service import ChildService
from schemas.child_schemas import ChildCreate, ChildResponse, ChildUpdate

router = APIRouter(prefix="/children", tags=["Children"])


def get_child_service(db: Session = Depends(get_db)) -> ChildService:
    return ChildService(db)


@router.post("/", response_model=ChildResponse)
async def create_child(
    child_data: ChildCreate,
    parent_id: int,
    child_service: ChildService = Depends(get_child_service)
):
    """Создать ребенка"""
    child = child_service.create_child(
        parent_id=parent_id,
        name=child_data.name,
        date_of_birth=child_data.date_of_birth,
        gender=child_data.gender,
        has_limitations=child_data.has_limitations,
        comment=child_data.comment
    )
    return ChildResponse.model_validate(child)


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(
    child_id: int,
    child_service: ChildService = Depends(get_child_service)
):
    """Получить ребенка по ID с интересами и навыками"""
    child = child_service.get_child_by_id(child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    return child


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: int,
    update_data: ChildUpdate,
    child_service: ChildService = Depends(get_child_service)
):
    """Обновить ребенка (включая интересы и навыки)"""
    child = child_service.update_child(child_id, update_data)
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    return child


@router.delete("/{child_id}")
async def delete_child(
    child_id: int,
    child_service: ChildService = Depends(get_child_service)
):
    """Удалить ребенка"""
    success = child_service.delete_child(child_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    return {"message": "Ребенок удален"} 