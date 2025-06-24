from dataclasses import dataclass
from typing import Optional
from models.user import User
from core.interfaces import IUserRepository, IOTPService


@dataclass
class RegisterUserCommand:
    """Команда для регистрации пользователя"""
    phone_number: str
    verification_code: str


@dataclass 
class RegisterUserResult:
    """Результат регистрации пользователя"""
    user: Optional[User]
    success: bool
    error_message: Optional[str] = None


class RegisterUserUseCase:
    """Use case для регистрации пользователя"""
    
    def __init__(self, user_repo: IUserRepository, otp_service: IOTPService):
        self._user_repo = user_repo
        self._otp_service = otp_service
    
    def execute(self, command: RegisterUserCommand) -> RegisterUserResult:
        """Выполняет регистрацию пользователя"""
        
        # Проверяем OTP код
        if not self._otp_service.verify_code(command.phone_number, command.verification_code):
            return RegisterUserResult(
                user=None,
                success=False,
                error_message="Неверный код подтверждения"
            )
        
        # Проверяем существующего пользователя
        existing_user = self._user_repo.get_by_phone(command.phone_number)
        if existing_user:
            return RegisterUserResult(
                user=existing_user,
                success=True
            )
        
        # Создаем нового пользователя
        new_user = User(phone_number=command.phone_number)
        created_user = self._user_repo.create(new_user)
        
        return RegisterUserResult(
            user=created_user,
            success=True
        ) 