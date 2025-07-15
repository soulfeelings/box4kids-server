from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.subscription import SubscriptionStatus


class SubscriptionCreateRequest(BaseModel):
    """Схема для создания подписки"""
    child_id: int = Field(..., description="ID ребенка")
    plan_id: int = Field(..., description="ID плана подписки")
    delivery_info_id: Optional[int] = Field(default=None, description="ID адреса доставки")


class SubscriptionUpdateRequest(BaseModel):
    """Схема для обновления подписки"""
    child_id: Optional[int] = Field(default=None, description="ID ребенка")
    plan_id: Optional[int] = Field(default=None, description="ID плана подписки")
    delivery_info_id: Optional[int] = Field(default=None, description="ID адреса доставки")
    status: Optional[SubscriptionStatus] = Field(default=None, description="Статус подписки")
    discount_percent: Optional[float] = Field(default=None, description="Процент скидки")
    expires_at: Optional[datetime] = Field(default=None, description="Дата истечения")


class SubscriptionResponse(BaseModel):
    """Схема ответа с данными подписки"""
    id: int
    child_id: int
    plan_id: int
    delivery_info_id: Optional[int]
    status: SubscriptionStatus
    discount_percent: float
    created_at: datetime
    expires_at: Optional[datetime]
    is_paused: bool = Field(default=False, description="Приостановлена ли подписка")
    
    class Config:
        from_attributes = True


class SubscriptionWithDetailsResponse(BaseModel):
    """Схема ответа с подробными данными подписки"""
    id: int
    child_id: int
    plan_id: int
    delivery_info_id: Optional[int]
    status: SubscriptionStatus
    discount_percent: float
    created_at: datetime
    expires_at: Optional[datetime]
    is_paused: bool = Field(default=False, description="Приостановлена ли подписка")
    child_name: str
    plan_name: str
    plan_price: float
    user_id: int
    user_name: Optional[str]
    
    class Config:
        from_attributes = True


class PauseSubscriptionResponse(BaseModel):
    """Схема ответа при приостановке подписки"""
    message: str = Field(..., description="Сообщение о результате операции")


class ResumeSubscriptionResponse(BaseModel):
    """Схема ответа при возобновлении подписки"""
    message: str = Field(..., description="Сообщение о результате операции")


class SubscriptionListResponse(BaseModel):
    """Схема для списка подписок"""
    subscriptions: list[SubscriptionWithDetailsResponse]
    total_count: int
    active_count: int 