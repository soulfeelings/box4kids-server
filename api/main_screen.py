from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from services.child_service import ChildService

router = APIRouter(prefix="/main", tags=["Main Screen"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


def get_child_service(db: Session = Depends(get_db)) -> ChildService:
    return ChildService(db)


@router.get("/dashboard/{user_id}")
async def get_main_screen_data(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    child_service: ChildService = Depends(get_child_service)
):
    """Получает агрегированные данные для главного экрана"""
    
    # Проверяем существование пользователя
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем данные
    active_subscription = subscription_service.get_active_subscription(user_id)
    children = child_service.get_children_by_parent(user_id)
    
    # Формируем ответ
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "phone": user.phone_number
        },
        "subscription": {
            "active": active_subscription is not None,
            "plan_name": active_subscription.plan_name if active_subscription else None,
            "expires_at": active_subscription.expires_at if active_subscription else None
        } if active_subscription else None,
        "children": [
            {
                "id": child.id,
                "name": child.name,
                "age": child.age,
                "gender": child.gender.value
            } for child in children
        ],
        "next_delivery": None,  # TODO: Добавить логику доставок
        "recommendations": []   # TODO: Добавить рекомендации игрушек
    } 