import hashlib
from core.config import settings


def verify_click_signature(
    click_trans_id: str,
    service_id: str,
    merchant_trans_id: str,
    merchant_prepare_id: str,
    amount: int,
    action: int,
    sign_time: str,
    received_signature: str
) -> bool:
    """Проверить подпись Click callback"""
    if settings.ENVIRONMENT == "development":
        return True
    
    # Формируем строку для подписи согласно документации Click
    sign_string = f"{click_trans_id}{service_id}{settings.CLICK_SECRET_KEY}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
    calculated_sign = hashlib.md5(sign_string.encode()).hexdigest()
    
    return calculated_sign == received_signature
