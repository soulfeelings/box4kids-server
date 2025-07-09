from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from models.toy_box import ToyBoxStatus


class ToyBoxItemResponse(BaseModel):
    """Элемент состава набора"""
    id: int
    toy_category_id: int
    quantity: int
    
    class Config:
        from_attributes = True


class ToyBoxReviewResponse(BaseModel):
    """Отзыв на набор"""
    id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ToyBoxResponse(BaseModel):
    """Ответ с набором игрушек"""
    id: int
    subscription_id: int
    child_id: int
    delivery_info_id: Optional[int] = None
    status: ToyBoxStatus
    delivery_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    created_at: datetime
    items: List[ToyBoxItemResponse] = []
    reviews: List[ToyBoxReviewResponse] = []
    
    class Config:
        from_attributes = True


class NextBoxItemResponse(BaseModel):
    """Элемент следующего набора (генерируется на лету)"""
    category_id: int
    category_name: str
    category_icon: Optional[str] = None
    quantity: int


class NextBoxResponse(BaseModel):
    """Следующий набор (генерируется на лету)"""
    items: List[NextBoxItemResponse]
    delivery_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    message: str


class ToyBoxCreateRequest(BaseModel):
    """Запрос на создание набора"""
    subscription_id: int


class ToyBoxReviewRequest(BaseModel):
    """Запрос на добавление отзыва"""
    rating: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5")
    comment: Optional[str] = Field(None, max_length=500, description="Комментарий к отзыву")


class ToyBoxListResponse(BaseModel):
    """Список наборов"""
    boxes: List[ToyBoxResponse] 