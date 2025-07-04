from functools import lru_cache
from core.interfaces import IOTPStorage
from core.config import settings
from .otp_storage import InMemoryOTPStorage, RedisOTPStorage


@lru_cache()
def get_otp_storage() -> IOTPStorage:
    """Создает singleton экземпляр OTP storage в зависимости от конфигурации"""
    if settings.OTP_STORAGE_TYPE == "redis":
        print(f"Используется Redis OTP storage: {settings.REDIS_URL}")
        return RedisOTPStorage(settings.REDIS_URL)
    else:
        print("Используется In-Memory OTP storage")
        return InMemoryOTPStorage() 