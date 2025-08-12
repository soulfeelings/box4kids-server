from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date as date_type


class DeliveryInfoBase(BaseModel):
    """Базовая схема для адреса доставки"""
    name: str = Field(..., description="Название адреса (Дом, Работа, и т.д.)")
    address: str = Field(..., description="Полный адрес доставки")
    date: date_type = Field(..., description="Дата доставки")
    time: str = Field(..., description="Предпочтительное время доставки")
    courier_comment: Optional[str] = Field(None, description="Комментарий для курьера")


class DeliveryInfoCreate(DeliveryInfoBase):
    """Схема для создания нового адреса доставки"""
    pass


class DeliveryInfoUpdate(BaseModel):
    """Схема для обновления адреса доставки"""
    name: Optional[str] = Field(None, description="Название адреса")
    address: Optional[str] = Field(None, description="Полный адрес доставки")
    date: Optional[date_type] = Field(None, description="Дата доставки")
    time: Optional[str] = Field(None, description="Предпочтительное время доставки")
    courier_comment: Optional[str] = Field(None, description="Комментарий для курьера")


class DeliveryInfoResponse(DeliveryInfoBase):
    """Схема ответа с данными адреса доставки"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeliveryInfoListResponse(BaseModel):
    """Список адресов доставки"""
    addresses: List[DeliveryInfoResponse] 