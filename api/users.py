from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core.security import get_current_user
from core.i18n import translate
from services.user_service import UserService
from services.child_service import ChildService
from schemas import UserProfileUpdateRequest, UserProfileResponse, UserProfileUpdateResponse, ChildResponse
from schemas.auth_schemas import UserFromToken

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_child_service(db: Session = Depends(get_db)) -> ChildService:
    return ChildService(db)


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: UserFromToken = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    request: Request = None
):
    lang = request.state.lang if request and hasattr(request.state, 'lang') else 'ru'
    user = user_service.get_user_by_id(current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail=translate('user_not_found', lang))
    
    return user


@router.put("/profile", response_model=UserProfileUpdateResponse)
async def update_user_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: UserFromToken = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    request: Request = None
):
    lang = request.state.lang if request and hasattr(request.state, 'lang') else 'ru'
    user = user_service.update_user_profile(current_user.id, profile_data.name)
    if not user:
        raise HTTPException(status_code=404, detail=translate('user_not_found', lang))
    
    return user


@router.get("/children", response_model=List[ChildResponse])
async def get_user_children(
    current_user: UserFromToken = Depends(get_current_user),
    child_service: ChildService = Depends(get_child_service)
):
    """Получает детей текущего пользователя с интересами и навыками"""
    children = child_service.get_children_by_parent(current_user.id)
    return children 