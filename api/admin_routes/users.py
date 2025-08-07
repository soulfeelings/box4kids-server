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
from models.subscription import SubscriptionStatus
from typing import List
from schemas.admin_schemas import (
    AdminUserResponse, 
    ChildWithBoxesResponse, 
    AdminDashboardResponse,
    AdminUserDetailResponse
)
from schemas.toy_box_schemas import ToyBoxResponse, NextBoxResponse, ToyBoxItemResponse, NextBoxItemResponse

router = APIRouter(prefix="/admin", tags=["Admin Users"])

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    current_admin: dict = Depends(get_current_admin),
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db)),
    subscription_service: SubscriptionService = Depends(lambda db=Depends(get_db): SubscriptionService(db)),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """Получает статистику для дашборда админки"""
    
    # Получаем всех пользователей
    users = user_service.get_all_users()
    total_users = len(users)
    
    # Подсчитываем пользователей без подписки
    users_without_subscription = 0
    active_subscriptions = 0
    pending_subscriptions = 0
    
    for user in users:
        user_subscriptions = subscription_service.get_user_subscriptions(user.id)
        if not user_subscriptions:
            users_without_subscription += 1
        else:
            for subscription in user_subscriptions:
                if subscription.status == SubscriptionStatus.ACTIVE:
                    active_subscriptions += 1
                elif subscription.status in [SubscriptionStatus.PENDING_PAYMENT, SubscriptionStatus.PAUSED]:
                    pending_subscriptions += 1
    
    # Подсчитываем активные наборы
    active_boxes = toy_box_service.get_active_boxes_count()
    
    return AdminDashboardResponse(
        total_users=total_users,
        active_subscriptions=active_subscriptions,
        pending_subscriptions=pending_subscriptions,
        active_boxes=active_boxes,
        users_without_subscription=users_without_subscription
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
        
        # Определяем статус подписки
        has_subscription = len(user_subscriptions) > 0
        subscription_status = None
        if has_subscription:
            # Берем статус самой активной подписки
            active_subscription = None
            for sub in user_subscriptions:
                if sub.status == SubscriptionStatus.ACTIVE:
                    active_subscription = sub
                    break
            if active_subscription:
                subscription_status = active_subscription.status.value
            elif user_subscriptions:
                subscription_status = user_subscriptions[0].status.value
        
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
                            quantity=item.quantity,
                            category_name=item.category.name if item.category else "Неизвестная категория"
                        ))
                
                current_box_response = ToyBoxResponse(
                    id=current_box.id,
                    subscription_id=current_box.subscription_id,
                    child_id=current_box.child_id,
                    status=current_box.status.value,
                    delivery_date=current_box.delivery_date,
                    return_date=current_box.return_date,
                    delivery_time=current_box.delivery_time,
                    return_time=current_box.return_time,
                    items=current_box_items
                )
            
            # Преобразуем next_box в схему
            next_box_response = None
            if next_box:
                next_box_items = []
                if next_box.items:
                    for item in next_box.items:
                        next_box_items.append(NextBoxItemResponse(
                            toy_category_id=item.toy_category_id,
                            quantity=item.quantity,
                            category_name=item.category_name
                        ))
                
                next_box_response = NextBoxResponse(
                    delivery_date=next_box.delivery_date,
                    return_date=next_box.return_date,
                    delivery_time=next_box.delivery_time,
                    return_time=next_box.return_time,
                    items=next_box_items
                )
            
            children_with_boxes.append(ChildWithBoxesResponse(
                id=child.id,
                name=child.name,
                date_of_birth=str(child.date_of_birth),
                gender=child.gender.value,
                has_limitations=child.has_limitations,
                comment=child.comment,
                current_box=current_box_response,
                next_box=next_box_response
            ))
        
        # Преобразуем адреса доставки в список словарей
        delivery_addresses_list = []
        for addr in delivery_addresses:
            delivery_addresses_list.append({
                "id": addr.id,
                "name": addr.name,
                "address": addr.address,
                "date": str(addr.date),
                "time": addr.time,
                "courier_comment": addr.courier_comment
            })
        
        # Создаем полный ответ для пользователя
        user_response = AdminUserResponse(
            id=user.id,
            name=user.name,
            phone_number=user.phone_number,
            role=user.role.value,
            created_at=user.created_at,
            has_subscription=has_subscription,
            subscription_status=subscription_status,
            children=children_with_boxes,
            delivery_addresses=delivery_addresses_list,
            subscriptions=user_subscriptions
        )
        
        result.append(user_response)
    
    return result

@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def get_user_detail(
    user_id: int,
    current_admin: dict = Depends(get_current_admin),
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db)),
    child_service: ChildService = Depends(lambda db=Depends(get_db): ChildService(db)),
    subscription_service: SubscriptionService = Depends(lambda db=Depends(get_db): SubscriptionService(db)),
    delivery_service: DeliveryInfoService = Depends(lambda db=Depends(get_db): DeliveryInfoService(db)),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """Получает детальную информацию о пользователе"""
    
    user = user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем детей пользователя
    children = child_service.get_children_by_parent(user.id)
    
    # Получаем адреса доставки
    delivery_addresses = delivery_service.get_user_addresses(user.id)
    
    # Получаем подписки пользователя
    user_subscriptions = subscription_service.get_user_subscriptions(user.id)
    
    # Определяем статус подписки
    has_subscription = len(user_subscriptions) > 0
    subscription_status = None
    if has_subscription:
        active_subscription = None
        for sub in user_subscriptions:
            if sub.status == SubscriptionStatus.ACTIVE:
                active_subscription = sub
                break
        if active_subscription:
            subscription_status = active_subscription.status.value
        elif user_subscriptions:
            subscription_status = user_subscriptions[0].status.value
    
    # Получаем текущие и следующие наборы для каждого ребенка
    children_with_boxes = []
    current_boxes = []
    next_boxes = []
    
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
                        quantity=item.quantity,
                        category_name=item.category.name if item.category else "Неизвестная категория"
                    ))
            
            current_box_response = ToyBoxResponse(
                id=current_box.id,
                subscription_id=current_box.subscription_id,
                child_id=current_box.child_id,
                status=current_box.status.value,
                delivery_date=current_box.delivery_date,
                return_date=current_box.return_date,
                delivery_time=current_box.delivery_time,
                return_time=current_box.return_time,
                items=current_box_items
            )
            current_boxes.append(current_box_response)
        
        # Преобразуем next_box в схему
        next_box_response = None
        if next_box:
            next_box_items = []
            if next_box.items:
                for item in next_box.items:
                    next_box_items.append(NextBoxItemResponse(
                        toy_category_id=item.toy_category_id,
                        quantity=item.quantity,
                        category_name=item.category_name
                    ))
            
            next_box_response = NextBoxResponse(
                delivery_date=next_box.delivery_date,
                return_date=next_box.return_date,
                delivery_time=next_box.delivery_time,
                return_time=next_box.return_time,
                items=next_box_items
            )
            next_boxes.append(next_box_response)
        
        children_with_boxes.append(ChildWithBoxesResponse(
            id=child.id,
            name=child.name,
            date_of_birth=str(child.date_of_birth),
            gender=child.gender.value,
            has_limitations=child.has_limitations,
            comment=child.comment,
            current_box=current_box_response,
            next_box=next_box_response
        ))
    
    # Преобразуем адреса доставки в список словарей
    delivery_addresses_list = []
    for addr in delivery_addresses:
        delivery_addresses_list.append({
            "id": addr.id,
            "name": addr.name,
            "address": addr.address,
            "date": str(addr.date),
            "time": addr.time,
            "courier_comment": addr.courier_comment
        })
    
    return AdminUserDetailResponse(
        id=user.id,
        name=user.name,
        phone_number=user.phone_number,
        role=user.role.value,
        created_at=user.created_at,
        has_subscription=has_subscription,
        subscription_status=subscription_status,
        children=children_with_boxes,
        delivery_addresses=delivery_addresses_list,
        subscriptions=user_subscriptions,
        current_boxes=current_boxes,
        next_boxes=next_boxes
    )

@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: int,
    new_role: str,
    current_admin: dict = Depends(get_current_admin),
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db))
):
    """Изменить роль пользователя"""
    try:
        role = UserRole(new_role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверная роль")
    
    user = user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_service.update_role(user_id, role)
    return {"message": "Роль пользователя изменена"}

@router.put("/toy-boxes/{box_id}/status")
async def update_toy_box_status(
    box_id: int,
    new_status: str,
    current_admin: dict = Depends(get_current_admin),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """Обновить статус набора игрушек"""
    from models.toy_box import ToyBoxStatus
    
    try:
        status = ToyBoxStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный статус")
    
    box = toy_box_service.update_box_status(box_id, status)
    if not box:
        raise HTTPException(status_code=404, detail="Набор не найден")
    
    return {"message": "Статус набора обновлен"} 