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
        logger.info(f"📱 [OTP] Generating OTP code for phone: {phone}")
        
        # Генерируем случайный 4-значный код
        code = str(random.randint(1000, 9999))
        logger.info(f"📱 [OTP] Generated OTP code: {code} for {phone}")
        
        # Сохраняем код через storage
        logger.info(f"📱 [OTP] Storing OTP code in storage for {phone}")
        success = self.storage.store_code(phone, code)
        
        if not success:
            logger.error(f"🔴 [OTP] Failed to store OTP code for {phone}")
            return False
        
        logger.info(f"📱 [OTP] OTP code stored successfully for {phone}")
        
        # Если SMS отключена (dev режим) - только логируем
        if not settings.SMS_ENABLED:
            logger.info(f"📱 [OTP] [DEV MODE] SMS disabled. OTP code for {phone}: {code}")
            return True
        
        # Production: отправляем SMS
        try:
            sms_text = f"Box4Kids OTP: {code}"
            logger.info(f"📱 [OTP] Sending SMS to {phone}")
            await SMSGateway.send_single_sms(phone, sms_text)
            logger.info(f"✅ [OTP] SMS with OTP code sent successfully to {phone}")
            return True
        except Exception as e:
            logger.error(f"🔴 [OTP] Error sending SMS to {phone}: {str(e)}", exc_info=True)
            # В случае ошибки SMS удаляем сохраненный код
            logger.info(f"📱 [OTP] Deleting stored code due to SMS error for {phone}")
            self.storage.delete_code(phone)
            return False
    
    def verify_code(self, phone: str, code: str) -> bool:
        """Проверяет OTP код"""
        logger.info(f"🔍 [OTP] Verifying OTP code for phone: {phone}, code: {code}")
        
        stored_data = self.storage.get_code_data(phone)
        
        if not stored_data:
            logger.warning(f"⚠️ [OTP] No stored code found for {phone}")
            return False
        
        logger.info(f"🔍 [OTP] Found stored data for {phone}: attempts={stored_data.get('attempts', 0)}")
        
        # Проверяем количество попыток
        if stored_data["attempts"] >= settings.OTP_MAX_ATTEMPTS:
            logger.warning(f"⚠️ [OTP] Max attempts exceeded for {phone}: {stored_data['attempts']}/{settings.OTP_MAX_ATTEMPTS}")
            self.storage.delete_code(phone)
            return False
        
        # Проверяем время (код действителен OTP_TTL_SECONDS)
        time_elapsed = time.time() - stored_data["timestamp"]
        if time_elapsed > settings.OTP_TTL_SECONDS:
            logger.warning(f"⚠️ [OTP] Code expired for {phone}: {time_elapsed:.1f}s > {settings.OTP_TTL_SECONDS}s")
            self.storage.delete_code(phone)
            return False
        
        logger.info(f"🔍 [OTP] Code is valid (time check passed): {time_elapsed:.1f}s < {settings.OTP_TTL_SECONDS}s")
        
        # Увеличиваем счетчик попыток
        attempts = self.storage.increment_attempts(phone)
        logger.info(f"🔍 [OTP] Incremented attempts for {phone}: {attempts}")
        
        # Проверяем код
        if stored_data["code"] == code:
            logger.info(f"✅ [OTP] Code verification successful for {phone}")
            self.storage.delete_code(phone)  # Удаляем использованный код
            return True
        
        logger.warning(f"❌ [OTP] Code verification failed for {phone}. Attempt {attempts}/{settings.OTP_MAX_ATTEMPTS}")
        return False 