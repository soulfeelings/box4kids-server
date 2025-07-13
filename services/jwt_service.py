from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import lru_cache
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import settings


class JWTService:
    """Сервис для работы с JWT токенами"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = 30  # Refresh token живет 30 дней
    
    def create_access_token(self, user_id: int, phone_number: str, name: Optional[str] = None) -> str:
        """Создает access token для пользователя"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": str(user_id),
            "phone": phone_number,
            "name": name,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int) -> str:
        """Создает refresh token для пользователя"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверяет и декодирует токен"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def extract_user_id(self, token: str) -> Optional[int]:
        """Извлекает ID пользователя из токена"""
        payload = self.verify_token(token)
        if payload and payload.get("sub"):
            try:
                return int(payload["sub"])
            except ValueError:
                return None
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """Проверяет, истек ли токен"""
        payload = self.verify_token(token)
        if not payload:
            return True
        
        exp = payload.get("exp")
        if not exp:
            return True
        
        return datetime.fromtimestamp(exp) < datetime.utcnow()


@lru_cache()
def get_jwt_service() -> JWTService:
    """Создает единый экземпляр JWTService для всего приложения"""
    return JWTService() 