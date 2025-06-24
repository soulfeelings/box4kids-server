from pydantic import BaseModel, Field
from typing import Optional, List
from .child_schemas import ChildResponse


class UserProfileUpdate(BaseModel):
    name: str = Field(..., description="Имя пользователя")


class UserProfileResponse(BaseModel):
    id: int
    phone_number: str
    name: Optional[str] = None
    role: str
    children: List[ChildResponse] = []
    
    class Config:
        from_attributes = True 