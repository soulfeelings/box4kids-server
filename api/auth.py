from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from functools import lru_cache
from core.database import get_db
from services import AuthService
from services.user_service import UserService
from services.otp_service import OTPService
from services.otp_factory import get_otp_storage
from services.jwt_service import get_jwt_service
from schemas import PhoneRequest, OTPRequest, UserResponse, DevGetCodeResponse
from schemas.auth_schemas import (
    AuthResponse, 
    RefreshTokenRequest, 
    TokenResponse,
    InitiatePhoneChangeRequest,
    ConfirmPhoneChangeRequest,
    UserFromToken
)
from core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@lru_cache()
def get_otp_service() -> OTPService:
    """Создает единый экземпляр OTPService для всего приложения"""
    storage = get_otp_storage()
    return OTPService(storage)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    otp_service = get_otp_service()
    return AuthService(db, otp_service)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


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


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(
    request: OTPRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Проверяет OTP код и создает/возвращает пользователя с токенами"""
    user = auth_service.verify_otp_and_create_user(
        request.phone_number, 
        request.code
    )
    
    if not user:
        print(f"API /verify-otp: Неверный код для {request.phone_number}")
        raise HTTPException(status_code=400, detail="Неверный код")
    
    # Создаем токены
    tokens = auth_service.create_tokens_for_user(user)
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        **tokens
    ) 


@router.post("/change-phone/initiate")
async def initiate_phone_change(
    request: InitiatePhoneChangeRequest,
    current_user: UserFromToken = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Инициация смены номера телефона - проверяет текущий номер и отправляет OTP на новый"""
    success = auth_service.initiate_phone_change(
        current_user.id,
        current_user.phone_number,
        request.current_phone_code,
        request.new_phone
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось инициировать смену номера")
    
    return {"message": "Код отправлен на новый номер"}


@router.post("/change-phone/confirm", response_model=AuthResponse)
async def confirm_phone_change(
    request: ConfirmPhoneChangeRequest,
    current_user: UserFromToken = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Подтверждение смены номера - проверяет OTP нового номера и обновляет пользователя"""
    user = auth_service.confirm_phone_change(
        current_user.id,
        request.new_phone,
        request.new_phone_code
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="Неверный код для нового номера")
    
    # Создаем новые токены с обновленным номером
    tokens = auth_service.create_tokens_for_user(user)
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        **tokens
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """Обновляет access токен используя refresh токен"""
    jwt_service = get_jwt_service()
    
    # Проверяем refresh токен
    payload = jwt_service.verify_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный refresh токен")
    
    # Проверяем тип токена
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Неверный тип токена")
    
    # Извлекаем ID пользователя
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Недействительный refresh токен")
    
    # Получаем пользователя из БД
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    # Создаем новые токены
    new_tokens = auth_service.create_tokens_for_user(user)
    
    return TokenResponse(**new_tokens) 