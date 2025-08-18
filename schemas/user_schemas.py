from pydantic import BaseModel, Field
from typing import Optional


class UserProfileUpdateRequest(BaseModel):
    name: str = Field(..., description="Имя пользователя")


class UserProfileUpdateResponse(BaseModel):
    id: int
    phone_number: str
    name: str
    role: str
    
    class Config:
        from_attributes = True 


class UserProfileResponse(BaseModel):
    id: int
    phone_number: str
    name: Optional[str] = None
    role: str
    
    class Config:
        from_attributes = True 