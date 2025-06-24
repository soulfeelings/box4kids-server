from typing import Optional
from sqlalchemy.orm import Session
from models.payment import Payment, PaymentStatus
from core.interfaces import IPaymentService
import uuid
import random


class MockPaymentService(IPaymentService):
    """Мокированный сервис для обработки платежей"""
    
    def __init__(self, db: Session):
        self._db = db
    
    def create_payment(self, user_id: int, subscription_id: int, amount: float) -> int:
        """Создает новый платеж и возвращает ID"""
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            external_payment_id=str(uuid.uuid4())
        )
        
        self._db.add(payment)
        self._db.commit()
        self._db.refresh(payment)
        
        return payment.id
    
    def process_payment(self, payment_id: int) -> bool:
        """Обрабатывает платеж (мок)"""
        payment = self._db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            return False
        
        # Мокируем успешность платежа (90% успешных)
        is_success = random.random() < 0.9
        
        payment.status = PaymentStatus.COMPLETED if is_success else PaymentStatus.FAILED
        self._db.commit()
        
        status_text = "успешно обработан" if is_success else "не прошел"
        print(f"[MOCK] Платеж {payment_id} {status_text}")
        
        return is_success
    
    def get_payment_status(self, payment_id: int) -> Optional[str]:
        """Получает статус платежа"""
        payment = self._db.query(Payment).filter(Payment.id == payment_id).first()
        return payment.status.value if payment else None 