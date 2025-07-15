from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_admin
from services.user_service import UserService
from services.child_service import ChildService
from services.subscription_service import SubscriptionService
from services.delivery_info_service import DeliveryInfoService
from services.toy_box_service import ToyBoxService
from models.user import UserRole
from typing import List
from datetime import datetime, timedelta
from jose import jwt, JWTError
from pydantic import BaseModel
from schemas.admin_schemas import AdminUserResponse, ChildWithBoxesResponse
from schemas.toy_box_schemas import ToyBoxResponse, NextBoxResponse, ToyBoxItemResponse, NextBoxItemResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

# Импортируем константы из core.security
from core.security import ADMIN_JWT_SECRET, ADMIN_JWT_ALGORITHM

class AdminLoginRequest(BaseModel):
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

def verify_admin_password(password: str):
    """Проверяет пароль администратора"""
    if password != "123456":
        raise HTTPException(status_code=403, detail="Неверный пароль")
    return True

def create_admin_token():
    """Создает JWT токен для админа"""
    expiration = datetime.utcnow() + timedelta(hours=24)  # Токен на 24 часа
    payload = {
        "sub": "admin",
        "exp": expiration,
        "role": "admin"
    }
    token = jwt.encode(payload, ADMIN_JWT_SECRET, algorithm=ADMIN_JWT_ALGORITHM)
    return token, expiration

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Авторизация администратора"""
    verify_admin_password(request.password)
    
    token, expiration = create_admin_token()
    
    return AdminLoginResponse(
        access_token=token,
        expires_in=int((expiration - datetime.utcnow()).total_seconds())
    )

@router.get("/users", response_model=List[AdminUserResponse])
async def get_all_users(
    current_admin: dict = Depends(get_current_admin),
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db)),
    child_service: ChildService = Depends(lambda db=Depends(get_db): ChildService(db)),
    subscription_service: SubscriptionService = Depends(lambda db=Depends(get_db): SubscriptionService(db)),
    delivery_service: DeliveryInfoService = Depends(lambda db=Depends(get_db): DeliveryInfoService(db)),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """Получает всех пользователей с полной информацией для админки"""
    
    # Получаем всех пользователей
    users = user_service.get_all_users()
    
    # Для каждого пользователя собираем полную информацию
    result = []
    for user in users:
        # Получаем детей пользователя
        children = child_service.get_children_by_parent(user.id)
        
        # Получаем адреса доставки
        delivery_addresses = delivery_service.get_user_addresses(user.id)
        
        # Получаем подписки пользователя
        user_subscriptions = subscription_service.get_user_subscriptions(user.id)
        
        # Получаем текущие и следующие наборы для каждого ребенка
        children_with_boxes = []
        for child in children:
            current_box = toy_box_service.get_current_box_by_child(child.id)
            next_box = toy_box_service.generate_next_box_for_child(child.id)
            
            # Преобразуем current_box в схему
            current_box_response = None
            if current_box:
                current_box_items = []
                if hasattr(current_box, 'items') and current_box.items:
                    for item in current_box.items:
                        current_box_items.append(ToyBoxItemResponse(
                            id=item.id,
                            toy_category_id=item.toy_category_id,
                            quantity=item.quantity
                        ))
                
                current_box_response = ToyBoxResponse(
                    id=current_box.id,
                    subscription_id=current_box.subscription_id,
                    child_id=current_box.child_id,
                    delivery_info_id=current_box.delivery_info_id,
                    status=current_box.status,
                    delivery_date=current_box.delivery_date,
                    return_date=current_box.return_date,
                    delivery_time=current_box.delivery_time,
                    return_time=current_box.return_time,
                    created_at=current_box.created_at,
                    items=current_box_items
                )
            
            # Преобразуем next_box в схему
            next_box_response = None
            if next_box:
                next_box_items = []
                if next_box.items:
                    for item in next_box.items:
                        next_box_items.append(NextBoxItemResponse(
                            category_id=item.category_id,
                            category_name=item.category_name,
                            category_icon=item.category_icon,
                            quantity=item.quantity
                        ))
                
                next_box_response = NextBoxResponse(
                    items=next_box_items,
                    delivery_date=next_box.delivery_date,
                    return_date=next_box.return_date,
                    delivery_time=next_box.delivery_time,
                    return_time=next_box.return_time,
                    message=next_box.message
                )
            
            child_data = ChildWithBoxesResponse(
                id=child.id,
                name=child.name,
                date_of_birth=child.date_of_birth.isoformat(),
                gender=child.gender.value,
                has_limitations=child.has_limitations,
                comment=child.comment,
                current_box=current_box_response,
                next_box=next_box_response
            )
            children_with_boxes.append(child_data)
        
        # Формируем полную информацию о пользователе
        user_data = AdminUserResponse(
            id=user.id,
            phone_number=user.phone_number,
            name=user.name,
            role=user.role.value,
            created_at=user.created_at,
            children=children_with_boxes,
            delivery_addresses=delivery_addresses,
            subscriptions=user_subscriptions
        )
        
        result.append(user_data)
    
    return result

@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: int,
    new_role: str,
    current_admin: dict = Depends(get_current_admin),
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db))
):
    """Изменяет роль пользователя"""
    
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Неверная роль")
    
    user.role = UserRole.ADMIN if new_role == "admin" else UserRole.USER
    db = next(get_db())
    db.commit()
    return {"message": f"Роль пользователя изменена на {new_role}"}

@router.put("/toy-boxes/{box_id}/status")
async def update_toy_box_status(
    box_id: int,
    new_status: str,
    current_admin: dict = Depends(get_current_admin),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """Изменяет статус набора игрушек"""
    
    from models.toy_box import ToyBoxStatus
    
    # Проверяем что статус валидный
    valid_statuses = [status.value for status in ToyBoxStatus]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Неверный статус. Допустимые: {valid_statuses}")
    
    # Обновляем статус
    updated_box = toy_box_service.update_box_status(box_id, ToyBoxStatus(new_status))
    if not updated_box:
        raise HTTPException(status_code=404, detail="Набор не найден")
    
    return {"message": f"Статус набора изменен на {new_status}"}

