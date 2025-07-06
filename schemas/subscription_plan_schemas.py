from pydantic import BaseModel
from typing import List, Optional


class ToyCategoryConfigResponse(BaseModel):
    """Конфигурация категории игрушек в плане"""
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    quantity: int
    
    class Config:
        from_attributes = True


class SubscriptionPlanResponse(BaseModel):
    """Ответ с планом подписки"""
    id: int
    name: str
    price_monthly: float
    toy_count: int
    description: Optional[str] = None
    toy_configurations: List[ToyCategoryConfigResponse] = []
    
    class Config:
        from_attributes = True


class SubscriptionPlansListResponse(BaseModel):
    """Список планов подписки"""
    plans: List[SubscriptionPlanResponse] 