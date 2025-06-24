from typing import Dict
import random
import time


class OTPService:
    """Мокированный сервис для отправки OTP кодов"""
    
    def __init__(self):
        # В реальной жизни это будет Redis или другое хранилище
        self._codes: Dict[str, Dict] = {}
    
    def send_code(self, phone: str) -> bool:
        """Отправляет OTP код (мок)"""
        # Генерируем случайный 4-значный код
        code = str(random.randint(1000, 9999))
        
        # Сохраняем код с timestamp
        self._codes[phone] = {
            "code": code,
            "timestamp": time.time(),
            "attempts": 0
        }
        
        # В реальной жизни здесь будет отправка SMS
        print(f"[MOCK] SMS отправлена на {phone}: код {code}")
        
        return True
    
    def verify_code(self, phone: str, code: str) -> bool:
        """Проверяет OTP код"""
        if phone not in self._codes:
            return False
        
        stored_data = self._codes[phone]
        
        # Проверяем количество попыток
        if stored_data["attempts"] >= 3:
            del self._codes[phone]
            return False
        
        # Проверяем время (код действителен 5 минут)
        if time.time() - stored_data["timestamp"] > 300:
            del self._codes[phone]
            return False
        
        # Увеличиваем счетчик попыток
        stored_data["attempts"] += 1
        
        # Проверяем код
        if stored_data["code"] == code:
            del self._codes[phone]  # Удаляем использованный код
            return True
        
        return False 