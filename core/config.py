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
    
    # SMS Gateway (getsms.uz)
    SMS_LOGIN: str = os.getenv("SMS_LOGIN", "")
    SMS_PASSWORD: str = os.getenv("SMS_PASSWORD", "")
    SMS_NICKNAME: str = os.getenv("SMS_NICKNAME", "")
    SMS_ENABLED: bool = os.getenv("SMS_ENABLED", "false").lower() == "true"
    
    # Click Payment System
    CLICK_MERCHANT_ID: str = os.getenv("CLICK_MERCHANT_ID", "")
    CLICK_SECRET_KEY: str = os.getenv("CLICK_SECRET_KEY", "")
    CLICK_SERVICE_ID: str = os.getenv("CLICK_SERVICE_ID", "")
    CLICK_MERCHANT_USER_ID: str = os.getenv("CLICK_MERCHANT_USER_ID", "")
    
    # Payme Payment System
    PAYME_MERCHANT_ID: str = os.getenv("PAYME_MERCHANT_ID", "")
    PAYME_SECRET_KEY: str = os.getenv("PAYME_SECRET_KEY", "")
    PAYME_SUBSCRIBE_API_URL: str = os.getenv("PAYME_SUBSCRIBE_API_URL", "https://checkout.paycom.uz/api")
    PAYME_MERCHANT_API_URL: str = os.getenv("PAYME_MERCHANT_API_URL", "https://merchant.paycom.uz/api")
    PAYME_TEST_MODE: bool = os.getenv("PAYME_TEST_MODE", "true").lower() == "true"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # ToyBox periods (in days)
    INITIAL_DELIVERY_PERIOD: int = 7  # Первая доставка через 7 дней
    RENTAL_PERIOD: int = 14  # Период аренды 14 дней
    NEXT_DELIVERY_PERIOD: int = 1  # Следующая доставка через 1 день после возврата
    
    # Subscription settings
    SUBSCRIPTION_EXPIRING_NOTIFICATION_DAYS: int = 3  # Уведомление за 3 дня
    
    # Mock Payment Gateway settings
    MOCK_PAYMENT_SUCCESS_RATE: float = float(os.getenv("MOCK_PAYMENT_SUCCESS_RATE", "0.95"))  # 95% успех для тестирования
    
    # App
    APP_NAME: str = "Box4Kids"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    class Config:
        env_file = ".env"


settings = Settings() 