"""
Утилиты для работы с валютой и конвертации между сумами и тийинами.

В Узбекистане:
- 1 сум = 100 тийин
- Платежные системы (Click, Payme) работают с тийинами
- В базе данных храним суммы в сумах для удобства
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Union


def sums_to_tiyin(sums: Union[float, int, Decimal]) -> int:
    """
    Конвертировать сумы в тийины
    
    Args:
        sums: Сумма в сумах (может быть float, int или Decimal)
        
    Returns:
        int: Сумма в тийинах
        
    Raises:
        ValueError: Если сумма отрицательная или слишком большая
        
    Examples:
        >>> sums_to_tiyin(50000.0)
        5000000
        >>> sums_to_tiyin(123.45)
        12345
    """
    if sums < 0:
        raise ValueError(f"Amount cannot be negative: {sums}")
    
    # Максимальная сумма: 10 млн сум = 1 млрд тийин
    MAX_SUMS = 10_000_000
    if sums > MAX_SUMS:
        raise ValueError(f"Amount too large: {sums} (max: {MAX_SUMS})")
    
    # Используем Decimal для точности
    decimal_sums = Decimal(str(sums))
    decimal_tiyin = decimal_sums * 100
    
    # Округляем до ближайшего целого
    tiyin = int(decimal_tiyin.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    
    return tiyin


def tiyin_to_sums(tiyin: Union[int, float]) -> float:
    """
    Конвертировать тийины в сумы
    
    Args:
        tiyin: Сумма в тийинах
        
    Returns:
        float: Сумма в сумах
        
    Raises:
        ValueError: Если сумма отрицательная или слишком большая
        
    Examples:
        >>> tiyin_to_sums(5000000)
        50000.0
        >>> tiyin_to_sums(12345)
        123.45
    """
    if tiyin < 0:
        raise ValueError(f"Amount cannot be negative: {tiyin}")
    
    # Максимальная сумма: 1 млрд тийин = 10 млн сум
    MAX_TIYIN = 1_000_000_000
    if tiyin > MAX_TIYIN:
        raise ValueError(f"Amount too large: {tiyin} (max: {MAX_TIYIN})")
    
    return float(tiyin) / 100


def validate_amount_match(expected_sums: float, received_tiyin: int, tolerance_tiyin: int = 1) -> bool:
    """
    Проверить соответствие сумм с учетом возможных погрешностей округления
    
    Args:
        expected_sums: Ожидаемая сумма в сумах
        received_tiyin: Полученная сумма в тийинах
        tolerance_tiyin: Допустимая погрешность в тийинах (по умолчанию 1)
        
    Returns:
        bool: True если суммы совпадают в пределах погрешности
        
    Examples:
        >>> validate_amount_match(123.45, 12345)
        True
        >>> validate_amount_match(123.45, 12346, tolerance_tiyin=1)
        True
        >>> validate_amount_match(123.45, 12347, tolerance_tiyin=1)
        False
    """
    try:
        expected_tiyin = sums_to_tiyin(expected_sums)
        difference = abs(expected_tiyin - received_tiyin)
        
        if difference > tolerance_tiyin:
            logging.warning(
                f"Amount mismatch: expected {expected_tiyin} tiyin ({expected_sums} sums), "
                f"received {received_tiyin} tiyin, difference: {difference} tiyin"
            )
            return False
            
        return True
        
    except ValueError as e:
        logging.error(f"Error validating amount: {e}")
        return False


def format_amount_for_display(amount_sums: float) -> str:
    """
    Форматировать сумму для отображения пользователю
    
    Args:
        amount_sums: Сумма в сумах
        
    Returns:
        str: Отформатированная строка
        
    Examples:
        >>> format_amount_for_display(50000.0)
        "50,000 сум"
        >>> format_amount_for_display(123.45)
        "123.45 сум"
    """
    if amount_sums == int(amount_sums):
        # Целое число - показываем без десятичных
        return f"{int(amount_sums):,} сум".replace(",", " ")
    else:
        # Дробное число - показываем с десятичными
        return f"{amount_sums:,.2f} сум".replace(",", " ")


def is_valid_payment_amount(amount_sums: float) -> bool:
    """
    Проверить валидность суммы платежа
    
    Args:
        amount_sums: Сумма в сумах
        
    Returns:
        bool: True если сумма валидна
    """
    MIN_AMOUNT = 1000  # Минимум 1000 сум
    MAX_AMOUNT = 10_000_000  # Максимум 10 млн сум
    
    return MIN_AMOUNT <= amount_sums <= MAX_AMOUNT
