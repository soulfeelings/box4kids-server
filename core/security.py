from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.jwt_service import get_jwt_service
from schemas.auth_schemas import UserFromToken

# Bearer token схема
security = HTTPBearer()

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
