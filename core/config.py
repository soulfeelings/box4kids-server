from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/box4kids"
    TEST_DATABASE_URL: str = "sqlite:///:memory:"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # App
    APP_NAME: str = "Box4Kids"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings() 