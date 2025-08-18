import hmac
import hashlib
import logging
from core.config import settings


def verify_payme_signature(signature: str, body: bytes) -> bool:
    """
    Проверить подпись Payme callback
    
    Args:
        signature: Подпись из заголовка X-Paycom-Signature
        body: Тело запроса в байтах
        
    Returns:
        bool: True если подпись валидна
    """
    # В development режиме пропускаем проверку для удобства тестирования
    if settings.ENVIRONMENT == "development":
        logging.info("Skipping Payme signature verification in development mode")
        return True
    
    # В production всегда проверяем подпись
    if not settings.PAYME_SECRET_KEY:
        logging.error("PAYME_SECRET_KEY not configured for production")
        return False

    try:
        # Вычисляем HMAC-SHA256 от тела запроса
        calculated = hmac.new(
            settings.PAYME_SECRET_KEY.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        is_valid = calculated == signature
        
        if not is_valid:
            logging.warning("Invalid Payme signature received")
        
        return is_valid
        
    except Exception as e:
        logging.error(f"Error verifying Payme signature: {e}")
        return False