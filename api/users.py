from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from services.user_service import UserService
from services.child_service import ChildService
from schemas import UserProfileUpdate, UserProfileResponse, ChildResponse

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_child_service(db: Session = Depends(get_db)) -> ChildService:
    return ChildService(db)


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Получает профиль пользователя с детьми"""
    user = user_service.get_user_with_children(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user


@router.put("/profile/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: int,
    profile_data: UserProfileUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """Обновляет профиль пользователя"""
    user = user_service.update_user_profile(user_id, profile_data.name)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user


@router.get("/children/{parent_id}", response_model=List[ChildResponse])
async def get_user_children(
    parent_id: int,
    child_service: ChildService = Depends(get_child_service)
):
    """Получает детей пользователя с интересами и навыками"""
    children = child_service.get_children_by_parent(parent_id)
    return children 