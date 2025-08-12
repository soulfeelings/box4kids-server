import random
import time
from core.interfaces import IOTPStorage
from core.config import settings


class OTPService:
    """Сервис для отправки и проверки OTP кодов"""
    
    def __init__(self, storage: IOTPStorage):
        self.storage = storage
    
    def send_code(self, phone: str) -> bool:
        """Отправляет OTP код (мок)"""
        # Генерируем случайный 4-значный код
        code = str(random.randint(1000, 9999))
        
        # Сохраняем код через storage
        success = self.storage.store_code(phone, code)
        
        if success:
            # В реальной жизни здесь будет отправка SMS
            print(f"[MOCK] SMS отправлена на {phone}: код {code}")
            return True
        
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