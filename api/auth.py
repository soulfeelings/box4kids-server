from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services import AuthService, OTPService
from schemas import PhoneRequest, OTPRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    otp_service = OTPService()
    return AuthService(db, otp_service)


@router.post("/send-otp")
async def send_otp(
    request: PhoneRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Отправляет OTP код на указанный номер телефона"""
    success = auth_service.verify_phone(request.phone_number)
    
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось отправить код")
    
    return {"message": "Код отправлен"}


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
        raise HTTPException(status_code=400, detail="Неверный код")
    
    return user 