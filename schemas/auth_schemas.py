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