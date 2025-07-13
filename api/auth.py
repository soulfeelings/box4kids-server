from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from functools import lru_cache
from core.database import get_db
from services import AuthService
from services.otp_service import OTPService
from services.otp_factory import get_otp_storage
from schemas import PhoneRequest, OTPRequest, UserResponse, DevGetCodeResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@lru_cache()
def get_otp_service() -> OTPService:
    """Создает единый экземпляр OTPService для всего приложения"""
    storage = get_otp_storage()
    return OTPService(storage)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    otp_service = get_otp_service()
    return AuthService(db, otp_service)


@router.post("/send-otp")
async def send_otp(
    request: PhoneRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Отправляет OTP код на указанный номер телефона"""
    success = auth_service.verify_phone(request.phone_number)
    
    if not success:
        print(f"API /send-otp: Не удалось отправить код для {request.phone_number}")
        raise HTTPException(status_code=400, detail="Не удалось отправить код")
    
    return {"message": "Код отправлен"}

@router.post("/dev-get-code", response_model=DevGetCodeResponse)
async def dev_get_code(
    request: PhoneRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """DEV метод чтобы получить код для тестирования"""
    code = auth_service.dev_get_code(request.phone_number)
    if not code:
        raise HTTPException(status_code=400, detail="Не удалось получить код")
    
    return {"code": code}


@router.post("/verify-otp", response_model=UserResponse)
async def verify_otp(
    request: OTPRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Проверяет OTP код и создает/возвращает пользователя"""
    user = auth_service.verify_otp_and_create_user(
        request.phone_number, 
        request.code
    )
    
    if not user:
        print(f"API /verify-otp: Неверный код для {request.phone_number}")
        raise HTTPException(status_code=400, detail="Неверный код")
    
    return user 