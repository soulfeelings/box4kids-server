from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.jwt_service import get_jwt_service
from schemas.auth_schemas import UserFromToken
from jose import jwt, JWTError

# Bearer token схема
security = HTTPBearer()

# Секретный ключ для админского JWT (в продакшене должен быть в переменных окружения)
ADMIN_JWT_SECRET = "admin_secret_key_123"
ADMIN_JWT_ALGORITHM = "HS256"

__all__ = ["get_current_user", "get_current_admin", "ADMIN_JWT_SECRET", "ADMIN_JWT_ALGORITHM"]

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserFromToken:
    """Извлекает текущего пользователя из JWT токена - без запроса к БД"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Проверяем токен
    token = credentials.credentials
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(token)
    
    if not payload:
        raise credentials_exception
    
    # Проверяем тип токена
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Извлекаем данные из токена
    try:
        user = UserFromToken(
            id=int(payload["sub"]),
            phone_number=payload["phone"],
            name=payload.get("name")
        )
        return user
    except (KeyError, ValueError):
        raise credentials_exception

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Извлекает данные админа из JWT токена"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Проверяем токен
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=[ADMIN_JWT_ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return payload
    except JWTError:
        raise credentials_exception
