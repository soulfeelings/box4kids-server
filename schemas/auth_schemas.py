from pydantic import BaseModel, Field
from typing import Optional


class PhoneRequest(BaseModel):
    phone_number: str = Field(..., description="Номер телефона в формате +7XXXXXXXXXX")


class OTPRequest(BaseModel):
    phone_number: str = Field(..., description="Номер телефона")
    code: str = Field(..., description="OTP код")


class UserResponse(BaseModel):
    id: int
    phone_number: str
    name: Optional[str] = None
    role: str
    
    class Config:
        from_attributes = True 


class DevGetCodeResponse(BaseModel):
    code: str


# JWT схемы
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh токен для обновления")


class UserFromToken(BaseModel):
    """Пользователь из JWT токена - без запроса к БД"""
    id: int
    phone_number: str
    name: Optional[str] = None