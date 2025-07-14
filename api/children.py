from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import get_current_user
from services.child_service import ChildService
from services.subscription_service import SubscriptionService
from services.subscription_plan_service import SubscriptionPlanService
from schemas.child_schemas import ChildCreate, ChildResponse, ChildUpdate
from schemas.auth_schemas import UserFromToken
from schemas.subscription_schemas import SubscriptionCreateRequest

router = APIRouter(prefix="/children", tags=["Children"])


def get_child_service(db: Session = Depends(get_db)) -> ChildService:
    return ChildService(db)


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


def get_subscription_plan_service(db: Session = Depends(get_db)) -> SubscriptionPlanService:
    return SubscriptionPlanService(db)


@router.post("/", response_model=ChildResponse)
async def create_child(
    child_data: ChildCreate,
    current_user: UserFromToken = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать ребенка для текущего пользователя"""
    # Создаем все сервисы с одной сессией БД
    child_service = ChildService(db)
    subscription_service = SubscriptionService(db)
    plan_service = SubscriptionPlanService(db)
    
    # Создаем ребенка
    child = child_service.create_child(
        parent_id=current_user.id,
        name=child_data.name,
        date_of_birth=child_data.date_of_birth,
        gender=child_data.gender,
        has_limitations=child_data.has_limitations,
        comment=child_data.comment
    )
    
    # Создаем базовую подписку
    try:
        # Получаем первый план (обычно базовый)
        plans = plan_service.get_all_plans()
        
        if plans.plans:
            # Создаем подписку с первым планом
            subscription_request = SubscriptionCreateRequest(
                child_id=child.id,
                plan_id=plans.plans[0].id
            )
            subscription_service.create_subscription_order(subscription_request)
        
    except Exception as e:
        # Логируем ошибку, но не прерываем создание ребенка
        print(f"Ошибка при создании базовой подписки: {e}")
    
    # Получаем обновленного ребенка с подпиской из БД
    updated_child = child_service.get_child_by_id(child.id)
    if updated_child:
        print(f"Обновленный ребенок: {updated_child}")
        return updated_child
    else:
        # Если не удалось получить обновленного ребенка, возвращаем исходный
        print(f"Не удалось получить обновленного ребенка: {child.id}")
        return ChildResponse.model_validate(child)


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(
    child_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    child_service: ChildService = Depends(get_child_service)
):
    """Получить ребенка по ID с интересами и навыками"""
    child = child_service.get_child_by_id(child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    # Проверяем что ребенок принадлежит текущему пользователю
    if child.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому ребенку")
    
    return child


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: int,
    update_data: ChildUpdate,
    current_user: UserFromToken = Depends(get_current_user),
    child_service: ChildService = Depends(get_child_service)
):
    """Обновить ребенка (включая интересы и навыки)"""
    # Сначала проверяем что ребенок существует и принадлежит пользователю
    existing_child = child_service.get_child_by_id(child_id)
    if not existing_child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    if existing_child.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому ребенку")
    
    child = child_service.update_child(child_id, update_data)
    if not child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    return child


@router.delete("/{child_id}")
async def delete_child(
    child_id: int,
    current_user: UserFromToken = Depends(get_current_user),
    child_service: ChildService = Depends(get_child_service)
):
    """Удалить ребенка"""
    # Сначала проверяем что ребенок существует и принадлежит пользователю
    existing_child = child_service.get_child_by_id(child_id)
    if not existing_child:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    if existing_child.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому ребенку")
    
    success = child_service.delete_child(child_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ребенок не найден")
    
    return {"message": "Ребенок удален"} 