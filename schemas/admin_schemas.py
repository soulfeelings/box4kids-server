from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
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
    children: List[ChildWithBoxesResponse]
    delivery_addresses: DeliveryInfoListResponse
    subscriptions: List[SubscriptionWithDetailsResponse]


class AdminUsersListResponse(BaseModel):
    """Схема для списка пользователей в админке"""
    users: List[AdminUserResponse] 