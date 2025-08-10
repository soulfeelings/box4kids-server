from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# from core.security import get_current_admin  # Временно отключаем аутентификацию
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from services.toy_box_service import ToyBoxService
from core.database import get_db
from pathlib import Path

router = APIRouter(prefix="/admin-web", tags=["Admin Web"])

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Простая функция для демо без аутентификации
async def get_demo_admin():
    return {"user_id": 1, "role": "admin"}

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db)),
    subscription_service: SubscriptionService = Depends(lambda db=Depends(get_db): SubscriptionService(db)),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """Дашборд админки"""
    
    # Получаем статистику
    users = user_service.get_all_users()
    total_users = len(users)
    
    users_without_subscription = 0
    active_subscriptions = 0
    pending_subscriptions = 0
    
    for user in users:
        user_subscriptions = subscription_service.get_user_subscriptions(user.id)
        if not user_subscriptions:
            users_without_subscription += 1
        else:
            for subscription in user_subscriptions:
                if subscription.status.value == "active":
                    active_subscriptions += 1
                elif subscription.status.value in ["pending_payment", "paused"]:
                    pending_subscriptions += 1
    
    active_boxes = toy_box_service.get_active_boxes_count()
    
    stats = {
        "total_users": total_users,
        "active_subscriptions": active_subscriptions,
        "pending_subscriptions": pending_subscriptions,
        "active_boxes": active_boxes,
        "users_without_subscription": users_without_subscription
    }
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats
    })

@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db)),
    subscription_service: SubscriptionService = Depends(lambda db=Depends(get_db): SubscriptionService(db)),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """Страница пользователей админки"""
    
    # Получаем всех пользователей с полной информацией
    users = user_service.get_all_users()
    
    # Для каждого пользователя собираем информацию
    users_data = []
    for user in users:
        user_subscriptions = subscription_service.get_user_subscriptions(user.id)
        
        # Определяем статус подписки
        has_subscription = len(user_subscriptions) > 0
        subscription_status = None
        if has_subscription:
            active_subscription = None
            for sub in user_subscriptions:
                if sub.status.value == "active":
                    active_subscription = sub
                    break
            if active_subscription:
                subscription_status = active_subscription.status.value
            elif user_subscriptions:
                subscription_status = user_subscriptions[0].status.value
        
        # Получаем детей пользователя
        children = []
        for child in user.children:
            current_box = toy_box_service.get_current_box_by_child(child.id)
            next_box = toy_box_service.generate_next_box_for_child(child.id)

            current_box_data = None
            if current_box:
                current_box_data = {
                    "id": current_box.id,
                    "delivery_date": str(current_box.delivery_date) if current_box.delivery_date else None,
                    "return_date": str(current_box.return_date) if current_box.return_date else None,
                    "status": getattr(current_box, 'status', None),
                }
            
            # Подготовка данных следующего набора с ID и статусом, если есть
            next_box_data = None
            if next_box:
                next_box_data = {
                    "id": getattr(next_box, 'id', None),
                    "delivery_date": str(next_box.delivery_date) if next_box.delivery_date else None,
                    "return_date": str(next_box.return_date) if next_box.return_date else None,
                    "status": getattr(next_box, 'status', None),
                }
            
            children.append({
                "id": child.id,
                "name": child.name,
                "date_of_birth": str(child.date_of_birth),
                "gender": child.gender.value,
                "has_limitations": child.has_limitations,
                "comment": child.comment,
                "current_box": current_box_data,
                "next_box": next_box_data
            })
        
        # Получаем адреса доставки
        delivery_addresses = []
        for addr in user.delivery_addresses:
            delivery_addresses.append({
                "id": addr.id,
                "name": addr.name,
                "address": addr.address,
                "date": str(addr.date),
                "time": addr.time,
                "courier_comment": addr.courier_comment
            })
        
        users_data.append({
            "id": user.id,
            "name": user.name,
            "phone_number": user.phone_number,
            "role": user.role.value,
            "created_at": user.created_at,
            "has_subscription": has_subscription,
            "subscription_status": subscription_status,
            "children": children,
            "delivery_addresses": delivery_addresses,
            "subscriptions": user_subscriptions
        })
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "users": users_data
    })

@router.get("/subscriptions", response_class=HTMLResponse)
async def admin_subscriptions(request: Request):
    """Страница подписок админки"""
    return templates.TemplateResponse("admin/subscriptions.html", {
        "request": request
    })

@router.get("/delivery-dates", response_class=HTMLResponse)
async def admin_delivery_dates(request: Request):
    """Страница редактирования дат доставки"""
    return templates.TemplateResponse("admin/delivery_dates.html", {
        "request": request
    })


@router.get("/boxes", response_class=HTMLResponse)
async def admin_boxes(request: Request):
    """Страница наборов админки"""
    return templates.TemplateResponse("admin/boxes.html", {
        "request": request
    })

# API endpoints для AJAX запросов
@router.get("/api/dashboard")
async def api_dashboard(
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db)),
    subscription_service: SubscriptionService = Depends(lambda db=Depends(get_db): SubscriptionService(db)),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """API для дашборда"""
    
    # Получаем статистику
    users = user_service.get_all_users()
    total_users = len(users)
    
    users_without_subscription = 0
    active_subscriptions = 0
    pending_subscriptions = 0
    
    for user in users:
        user_subscriptions = subscription_service.get_user_subscriptions(user.id)
        if not user_subscriptions:
            users_without_subscription += 1
        else:
            for subscription in user_subscriptions:
                if subscription.status.value == "active":
                    active_subscriptions += 1
                elif subscription.status.value in ["pending_payment", "paused"]:
                    pending_subscriptions += 1
    
    active_boxes = toy_box_service.get_active_boxes_count()
    
    return {
        "total_users": total_users,
        "active_subscriptions": active_subscriptions,
        "pending_subscriptions": pending_subscriptions,
        "active_boxes": active_boxes,
        "users_without_subscription": users_without_subscription
    }

@router.get("/api/users/{user_id}")
async def api_user_detail(
    user_id: int,
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db)),
    subscription_service: SubscriptionService = Depends(lambda db=Depends(get_db): SubscriptionService(db)),
    toy_box_service: ToyBoxService = Depends(lambda db=Depends(get_db): ToyBoxService(db))
):
    """API для деталей пользователя"""
    
    user = user_service.get_by_id(user_id)
    if not user:
        return {"error": "User not found"}
    
    user_subscriptions = subscription_service.get_user_subscriptions(user.id)
    
    # Определяем статус подписки
    has_subscription = len(user_subscriptions) > 0
    subscription_status = None
    if has_subscription:
        active_subscription = None
        for sub in user_subscriptions:
            if sub.status.value == "active":
                active_subscription = sub
                break
        if active_subscription:
            subscription_status = active_subscription.status.value
        elif user_subscriptions:
            subscription_status = user_subscriptions[0].status.value
    
    # Получаем детей пользователя
    children = []
    for child in user.children:
        current_box = toy_box_service.get_current_box_by_child(child.id)
        next_box = toy_box_service.generate_next_box_for_child(child.id)
        
        current_box_data = None
        if current_box:
            current_box_data = {
                "id": current_box.id,
                "delivery_date": str(current_box.delivery_date) if current_box.delivery_date else None,
                "return_date": str(current_box.return_date) if current_box.return_date else None,
                "status": getattr(current_box, 'status', None),
            }

        next_box_data = None
        if next_box:
            next_box_data = {
                "id": getattr(next_box, 'id', None),
                "delivery_date": str(next_box.delivery_date) if next_box.delivery_date else None,
                "return_date": str(next_box.return_date) if next_box.return_date else None,
                "status": getattr(next_box, 'status', None),
            }
        
        children.append({
            "id": child.id,
            "name": child.name,
            "date_of_birth": str(child.date_of_birth),
            "gender": child.gender.value,
            "has_limitations": child.has_limitations,
            "comment": child.comment,
            "current_box": current_box_data,
            "next_box": next_box_data
        })
    
    # Получаем адреса доставки
    delivery_addresses = []
    for addr in user.delivery_addresses:
        delivery_addresses.append({
            "id": addr.id,
            "name": addr.name,
            "address": addr.address,
            "date": str(addr.date),
            "time": addr.time,
            "courier_comment": addr.courier_comment
        })
    
    return {
        "id": user.id,
        "name": user.name,
        "phone_number": user.phone_number,
        "role": user.role.value,
        "created_at": user.created_at,
        "has_subscription": has_subscription,
        "subscription_status": subscription_status,
        "children": children,
        "delivery_addresses": delivery_addresses,
        "subscriptions": user_subscriptions
    } 