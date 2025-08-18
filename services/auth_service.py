import logging
from sqlalchemy.orm import Session
from models.user import User
from .otp_service import OTPService
from .jwt_service import get_jwt_service
from core.config import settings
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session, otp_service: OTPService):
        self.db = db
        self.otp_service = otp_service
    
    async def verify_phone(self, phone: str) -> bool:
        """Отправляет OTP код на телефон"""
        return await self.otp_service.send_code(phone)

    def dev_get_code(self, phone: str) -> str | None:
        """DEV метод чтобы получить код для тестирования"""
        # Блокируем в production
        if not settings.DEBUG:
            logger.warning(f"Попытка использовать dev_get_code в production для {phone}")
            return None
            
        code_data = self.otp_service.storage.get_code_data(phone)
        if code_data:
            return code_data["code"]
        return None
    
    def dev_verify_code(self, phone: str, code: str) -> bool:
        """Проверяет OTP код (только для dev)"""
        # Блокируем в production
        if not settings.DEBUG:
            logger.warning(f"Попытка использовать dev_verify_code в production для {phone}")
            return False
            
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
    
    async def initiate_phone_change(self, user_id: int, current_phone: str, current_code: str, new_phone: str) -> bool:
        """Инициация смены номера телефона - проверяет текущий номер и отправляет OTP на новый"""
        # Получаем пользователя
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"AuthService: Пользователь с ID {user_id} не найден")
            return False
        
        # Проверяем что текущий номер совпадает
        if user.phone_number != current_phone:
            print(f"AuthService: Неверный текущий номер {current_phone} для пользователя {user_id}")
            return False
        
        # Проверяем OTP для текущего номера
        if not self.otp_service.verify_code(current_phone, current_code):
            print(f"AuthService: Неверный код {current_code} для текущего номера {current_phone}")
            return False
        
        # Проверяем что новый номер не занят другим пользователем
        existing_user = self.db.query(User).filter(User.phone_number == new_phone).first()
        if existing_user and existing_user.id != user_id:
            print(f"AuthService: Новый номер {new_phone} уже занят пользователем {existing_user.id}")
            return False
        
        # Отправляем OTP на новый номер
        success = await self.otp_service.send_code(new_phone)
        if success:
            print(f"AuthService: OTP отправлен на новый номер {new_phone} для пользователя {user_id}")
        else:
            print(f"AuthService: Не удалось отправить OTP на новый номер {new_phone}")
        
        return success
    
    def confirm_phone_change(self, user_id: int, new_phone: str, new_code: str) -> Optional[User]:
        """Подтверждение смены номера - проверяет OTP нового номера и обновляет пользователя"""
        # Получаем пользователя
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"AuthService: Пользователь с ID {user_id} не найден")
            return None
        
        # Проверяем OTP для нового номера
        if not self.otp_service.verify_code(new_phone, new_code):
            print(f"AuthService: Неверный код {new_code} для нового номера {new_phone}")
            return None
        
        # Проверяем что новый номер не занят другим пользователем
        existing_user = self.db.query(User).filter(User.phone_number == new_phone).first()
        if existing_user and existing_user.id != user_id:
            print(f"AuthService: Новый номер {new_phone} уже занят пользователем {existing_user.id}")
            return None
        
        # Обновляем номер телефона
        old_phone = user.phone_number
        user.phone_number = new_phone
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        
        print(f"AuthService: Номер телефона изменен с {old_phone} на {new_phone} для пользователя {user_id}")
        return user
    
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