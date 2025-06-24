from pydantic import BaseModel, Field
from typing import Optional


class ChildCreate(BaseModel):
    name: str = Field(..., description="Имя ребенка")
    age: int = Field(..., ge=1, le=18, description="Возраст ребенка")
    gender: str = Field(..., description="Пол ребенка: male или female")


class ChildResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    parent_id: int
    
    class Config:
        from_attributes = True


class ChildUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=1, le=18)
    gender: Optional[str] = None 