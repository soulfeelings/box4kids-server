import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/box4kids"
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # OTP Storage
    OTP_STORAGE_TYPE: str = "redis"  # memory | redis
    OTP_TTL_SECONDS: int = 300  # 5 минут
    OTP_MAX_ATTEMPTS: int = 3
    
    # ToyBox periods (in days)
    INITIAL_DELIVERY_PERIOD: int = 7  # Первая доставка через 7 дней
    RENTAL_PERIOD: int = 14  # Период аренды 14 дней
    NEXT_DELIVERY_PERIOD: int = 1  # Следующая доставка через 1 день после возврата
    
    # Subscription settings
    SUBSCRIPTION_EXPIRING_NOTIFICATION_DAYS: int = 3  # Уведомление за 3 дня
    
    # App
    APP_NAME: str = "Box4Kids"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings() 