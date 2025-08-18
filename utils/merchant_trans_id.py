from typing import List, Optional
from datetime import datetime
import json


def create_merchant_trans_id(payment_type: str, user_id: int, subscription_ids: List[int]) -> str:
    """Создать merchant_trans_id для платежа"""
    ids_str = "_".join(map(str, sorted(subscription_ids)))
    timestamp = int(datetime.now().timestamp())
    return f"{payment_type}_{user_id}_{ids_str}_{timestamp}"


def parse_merchant_trans_id(merchant_trans_id: str) -> Optional[int]:
    """Парсить merchant_trans_id и получить ID платежа"""
    # Для новой архитектуры используем прямой поиск в БД
    # Возвращаем None, поиск будет по самому merchant_trans_id
    return None
