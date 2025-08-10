from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from schemas.delivery_info_schemas import DeliveryInfoListResponse
from schemas.subscription_schemas import SubscriptionWithDetailsResponse
from schemas.toy_box_schemas import ToyBoxResponse, NextBoxResponse


class ChildWithBoxesResponse(BaseModel):
    """Схема для ребенка с наборами"""
    id: int
    name: str
    date_of_birth: str
    gender: str
    has_limitations: bool
    comment: Optional[str] = None
    current_box: Optional[ToyBoxResponse] = None
    next_box: Optional[NextBoxResponse] = None


class AdminUserResponse(BaseModel):
    """Схема для пользователя в админке"""
    id: int
    phone_number: str
    name: Optional[str] = None
    role: str
    created_at: datetime
    has_subscription: bool  # Зарегистрировался но не оформил подписку
    subscription_status: Optional[str] = None  # Статус подписки
    children: List[ChildWithBoxesResponse]
    delivery_addresses: List[dict]  # Адреса доставки
    subscriptions: List[SubscriptionWithDetailsResponse]


class AdminUsersListResponse(BaseModel):
    """Схема для списка пользователей в админке"""
    users: List[AdminUserResponse]


class AdminDashboardResponse(BaseModel):
    """Схема для дашборда админки"""
    total_users: int
    active_subscriptions: int
    pending_subscriptions: int
    active_boxes: int
    users_without_subscription: int


class AdminUserDetailResponse(BaseModel):
    """Детальная информация о пользователе для админки"""
    id: int
    phone_number: str
    name: Optional[str] = None
    role: str
    created_at: datetime
    has_subscription: bool
    subscription_status: Optional[str] = None
    children: List[ChildWithBoxesResponse]
    delivery_addresses: List[dict]
    subscriptions: List[SubscriptionWithDetailsResponse]
    current_boxes: List[ToyBoxResponse]
    next_boxes: List[NextBoxResponse] 