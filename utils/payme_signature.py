import hashlib
from core.config import settings


def verify_payme_signature(signature: str, body: str) -> bool:
    """Проверить подпись Payme callback"""
    if settings.ENVIRONMENT == "development":
        return True

    calculated = hashlib.sha256(f"{body}{settings.PAYME_SECRET_KEY}".encode()).hexdigest()
    return calculated == signature
