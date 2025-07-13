from sqlalchemy.orm import Session
from models.user import User
from .otp_service import OTPService
from .jwt_service import get_jwt_service
from typing import Optional, Dict


class AuthService:
    def __init__(self, db: Session, otp_service: OTPService):
        self.db = db
        self.otp_service = otp_service
    
    def verify_phone(self, phone: str) -> bool:
        """Отправляет OTP код на телефон"""
        return self.otp_service.send_code(phone)

    def dev_get_code(self, phone: str) -> str | None:
        """DEV метод чтобы получить код для тестирования"""
        code_data = self.otp_service.storage.get_code_data(phone)
        if code_data:
            return code_data["code"]
        return None
    
    def dev_verify_code(self, phone: str, code: str) -> bool:
        """Проверяет OTP код"""
        return self.otp_service.verify_code(phone, code)
    
    def verify_otp_and_create_user(self, phone: str, code: str) -> Optional[User]:
        """Проверяет OTP код и создает пользователя"""
        if not self.otp_service.verify_code(phone, code):
            print(f"AuthService: Код {code} для {phone} не прошел проверку")
            return None
        
        # Проверяем, существует ли пользователь
        existing_user = self.db.query(User).filter(User.phone_number == phone).first()
        if existing_user:
            print(f"AuthService: Пользователь {phone} уже существует")
            return existing_user
        
        # Создаем нового пользователя
        new_user = User(phone_number=phone)
        self.db.add(new_user)
        self.db.flush()  # Только flush для получения ID
        self.db.refresh(new_user)
        
        print(f"AuthService: Создан новый пользователь {phone}")
        return new_user
    
    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Получает пользователя по номеру телефона"""
        return self.db.query(User).filter(User.phone_number == phone).first()
    
    def create_tokens_for_user(self, user: User) -> Dict[str, str]:
        """Создает JWT токены для пользователя"""
        jwt_service = get_jwt_service()
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            phone_number=user.phone_number,
            name=user.name
        )
        refresh_token = jwt_service.create_refresh_token(user_id=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        } 