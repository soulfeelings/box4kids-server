from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from core.security import ADMIN_JWT_SECRET, ADMIN_JWT_ALGORITHM

router = APIRouter(prefix="/admin", tags=["Admin Auth"])

class AdminLoginRequest(BaseModel):
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

def verify_admin_password(password: str):
    """Проверяет пароль администратора"""
    if password != "123456":
        raise HTTPException(status_code=403, detail="Неверный пароль")
    return True

def create_admin_token():
    """Создает JWT токен для админа"""
    expiration = datetime.utcnow() + timedelta(hours=24)  # Токен на 24 часа
    payload = {
        "sub": "admin",
        "exp": expiration,
        "role": "admin"
    }
    token = jwt.encode(payload, ADMIN_JWT_SECRET, algorithm=ADMIN_JWT_ALGORITHM)
    return token, expiration

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Авторизация администратора"""
    verify_admin_password(request.password)
    
    token, expiration = create_admin_token()
    
    return AdminLoginResponse(
        access_token=token,
        expires_in=int((expiration - datetime.utcnow()).total_seconds())
    ) 