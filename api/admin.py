from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services.user_service import UserService
from models.user import UserRole
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])


def verify_admin(user_id: int, db: Session = Depends(get_db)):
    """Проверяет права администратора"""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    return user


@router.get("/users")
async def get_all_users(
    admin_user = Depends(verify_admin),
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db))
):
    """Получает всех пользователей (только для админов)"""
    users = user_service.get_all_users()
    return users


@router.get("/stats")
async def get_stats(
    admin_user = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Получает статистику платформы"""
    from models import User, Child, Subscription, Payment
    
    total_users = db.query(User).count()
    total_children = db.query(Child).count()
    active_subscriptions = db.query(Subscription).filter(Subscription.is_active == True).count()
    total_payments = db.query(Payment).count()
    
    return {
        "total_users": total_users,
        "total_children": total_children,
        "active_subscriptions": active_subscriptions,
        "total_payments": total_payments
    }


@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: int,
    new_role: str,
    admin_user = Depends(verify_admin),
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db))
):
    """Изменяет роль пользователя"""
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Неверная роль")
    
    user.role = UserRole.ADMIN if new_role == "admin" else UserRole.USER
    # Здесь нужно добавить метод save в UserService
    return {"message": f"Роль пользователя изменена на {new_role}"} 