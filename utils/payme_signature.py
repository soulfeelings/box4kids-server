import hmac
import hashlib
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
    if settings.ENVIRONMENT == "development":
        return True
    
    # Вычисляем HMAC-SHA256 от тела запроса
    calculated = hmac.new(
        settings.PAYME_SECRET_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return calculated == signature