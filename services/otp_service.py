from typing import Dict, Optional
import random
import time
import logging
from core.interfaces import IOTPStorage
from core.config import settings
from .sms_gateway import SMSGateway, SMSPayload

logger = logging.getLogger(__name__)


class OTPService:
    """Сервис для отправки и проверки OTP кодов"""
    
    def __init__(self, storage: IOTPStorage):
        self.storage = storage
    
    async def send_code(self, phone: str) -> bool:
        """Отправляет OTP код"""
        # Генерируем случайный 4-значный код
        code = str(random.randint(1000, 9999))
        
        # Сохраняем код через storage
        success = self.storage.store_code(phone, code)
        
        if not success:
            logger.error(f"Не удалось сохранить OTP код для {phone}")
            return False
        
        # Если SMS отключена (dev режим) - только логируем
        if not settings.SMS_ENABLED:
            logger.info(f"[DEV MODE] OTP код для {phone}: {code}")
            return True
        
        # Production: отправляем SMS
        try:
            sms_text = f"Box4Kids OTP: {code}"
            await SMSGateway.send_single_sms(phone, sms_text)
            logger.info(f"SMS с OTP кодом отправлена на {phone}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки SMS на {phone}: {str(e)}")
            # В случае ошибки SMS удаляем сохраненный код
            self.storage.delete_code(phone)
            return False
    
    def verify_code(self, phone: str, code: str) -> bool:
        """Проверяет OTP код"""
        stored_data = self.storage.get_code_data(phone)
        
        if not stored_data:
            print(f"Нет кода для {phone}")
            return False
        
        # Проверяем количество попыток
        if stored_data["attempts"] >= settings.OTP_MAX_ATTEMPTS:
            print(f"Превышено количество попыток для {phone}")
            self.storage.delete_code(phone)
            return False
        
        # Проверяем время (код действителен OTP_TTL_SECONDS)
        if time.time() - stored_data["timestamp"] > settings.OTP_TTL_SECONDS:
            print(f"Время истекло для {phone}")
            self.storage.delete_code(phone)
            return False
        
        # Увеличиваем счетчик попыток
        attempts = self.storage.increment_attempts(phone)
        
        # Проверяем код
        if stored_data["code"] == code:
            print(f"Код {code} для {phone} проверен успешно")
            self.storage.delete_code(phone)  # Удаляем использованный код
            return True
        
        print(f"Код {code} для {phone} не прошел проверку. Попытка {attempts}/{settings.OTP_MAX_ATTEMPTS}")
        return False 