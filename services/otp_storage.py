from typing import Dict, Optional
import time
import json
from core.interfaces import IOTPStorage
from core.config import settings


class InMemoryOTPStorage(IOTPStorage):
    """Реализация хранилища OTP кодов в памяти"""
    
    def __init__(self):
        self._codes: Dict[str, Dict] = {}
    
    def store_code(self, phone: str, code: str) -> bool:
        """Сохраняет код с timestamp"""
        self._codes[phone] = {
            "code": code,
            "timestamp": time.time(),
            "attempts": 0
        }
        return True
    
    def get_code_data(self, phone: str) -> Optional[Dict]:
        """Возвращает данные кода"""
        return self._codes.get(phone)
    
    def increment_attempts(self, phone: str) -> int:
        """Увеличивает счетчик попыток"""
        if phone in self._codes:
            self._codes[phone]["attempts"] += 1
            return self._codes[phone]["attempts"]
        return 0
    
    def delete_code(self, phone: str) -> bool:
        """Удаляет код"""
        if phone in self._codes:
            del self._codes[phone]
            return True
        return False


class RedisOTPStorage(IOTPStorage):
    """Реализация хранилища OTP кодов в Redis"""
    
    def __init__(self, redis_url: str):
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
        except ImportError:
            raise ImportError("Для Redis storage нужен пакет redis: pip install redis")
    
    def _get_key(self, phone: str) -> str:
        """Генерирует ключ для Redis"""
        return f"otp:{phone}"
    
    def store_code(self, phone: str, code: str) -> bool:
        """Сохраняет код с TTL"""
        key = self._get_key(phone)
        data = {
            "code": code,
            "timestamp": str(time.time()),
            "attempts": "0"
        }
        
        try:
            # Используем pipeline для атомарности
            pipe = self._redis.pipeline()
            pipe.hset(key, mapping=data)
            pipe.expire(key, settings.OTP_TTL_SECONDS)
            pipe.execute()
            return True
        except Exception as e:
            print(f"Redis error storing code: {e}")
            return False
    
    def get_code_data(self, phone: str) -> Optional[Dict]:
        """Возвращает данные кода"""
        key = self._get_key(phone)
        
        try:
            data = self._redis.hgetall(key)
            if not data:
                return None
            
            # Преобразуем строки обратно в числа
            return {
                "code": data["code"],
                "timestamp": float(data["timestamp"]),
                "attempts": int(data["attempts"])
            }
        except Exception as e:
            print(f"Redis error getting code: {e}")
            return None
    
    def increment_attempts(self, phone: str) -> int:
        """Увеличивает счетчик попыток"""
        key = self._get_key(phone)
        
        try:
            attempts = self._redis.hincrby(key, "attempts", 1)
            return attempts
        except Exception as e:
            print(f"Redis error incrementing attempts: {e}")
            return 0
    
    def delete_code(self, phone: str) -> bool:
        """Удаляет код"""
        key = self._get_key(phone)
        
        try:
            result = self._redis.delete(key)
            return result > 0
        except Exception as e:
            print(f"Redis error deleting code: {e}")
            return False 