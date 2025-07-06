from sqlalchemy.orm import Session
from repositories.payment_repository import PaymentRepository
from models.payment import Payment, PaymentStatus
from typing import List, Optional
import uuid
import random


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)

    def create_payment(self, user_id: int, subscription_id: int, amount: float, currency: str = "RUB") -> int:
        """Создает платеж"""
        # Генерируем внешний ID платежа (имитация реального API)
        external_payment_id = f"PAY_{uuid.uuid4().hex[:12].upper()}"
        
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            external_payment_id=external_payment_id
        )
        
        payment = self.payment_repo.create(payment)
        
        # Здесь была бы интеграция с реальным платежным сервисом
        # Например: payment_gateway.create_payment(payment)
        
        return payment.id

    def process_payment(self, payment_id: int) -> bool:
        """Обрабатывает платеж (моканная логика)"""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            return False
        
        if payment.status != PaymentStatus.PENDING:
            return False
        
        # Имитация обработки платежа (90% успех)
        success = random.random() < 0.9
        
        if success:
            self.payment_repo.update_status(payment_id, PaymentStatus.COMPLETED)
        else:
            self.payment_repo.update_status(payment_id, PaymentStatus.FAILED)
        
        return success

    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """Получает платеж по ID"""
        return self.payment_repo.get_by_id(payment_id)

    def get_user_payments(self, user_id: int) -> List[Payment]:
        """Получает все платежи пользователя"""
        return self.payment_repo.get_by_user_id(user_id)

    def get_subscription_payments(self, subscription_id: int) -> List[Payment]:
        """Получает все платежи по подписке"""
        return self.payment_repo.get_by_subscription_id(subscription_id)

    def refund_payment(self, payment_id: int) -> bool:
        """Возвращает платеж"""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment or payment.status != PaymentStatus.COMPLETED:
            return False
        
        # Здесь была бы интеграция с реальным платежным сервисом
        # payment_gateway.refund_payment(payment.external_payment_id)
        
        self.payment_repo.update_status(payment_id, PaymentStatus.REFUNDED)
        return True

    def webhook_handler(self, external_payment_id: str, status: str) -> bool:
        """Обработчик webhook от внешнего платежного сервиса"""
        payment = self.payment_repo.get_by_external_id(external_payment_id)
        if not payment:
            return False
        
        # Маппинг статусов внешнего сервиса
        status_mapping = {
            "succeeded": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
            "pending": PaymentStatus.PENDING
        }
        
        new_status = status_mapping.get(status)
        if new_status:
            self.payment_repo.update_status(payment.id, new_status)
            return True
        
        return False

    def get_pending_payments(self) -> List[Payment]:
        """Получает все платежи в ожидании"""
        return self.payment_repo.get_pending_payments()

    def retry_failed_payment(self, payment_id: int) -> bool:
        """Повторная попытка обработки платежа"""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment or payment.status != PaymentStatus.FAILED:
            return False
        
        # Сбрасываем статус в pending
        self.payment_repo.update_status(payment_id, PaymentStatus.PENDING)
        
        # Повторно обрабатываем
        return self.process_payment(payment_id)


# Сохраняем старый класс для обратной совместимости
MockPaymentService = PaymentService 