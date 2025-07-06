from sqlalchemy.orm import Session
from models.payment import Payment, PaymentStatus
from typing import List, Optional


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment: Payment) -> Payment:
        """Создает новый платеж"""
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Получает платеж по ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_by_user_id(self, user_id: int) -> List[Payment]:
        """Получает все платежи пользователя"""
        return self.db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(Payment.created_at.desc()).all()

    def get_by_subscription_id(self, subscription_id: int) -> List[Payment]:
        """Получает все платежи по подписке"""
        return self.db.query(Payment).filter(
            Payment.subscription_id == subscription_id
        ).order_by(Payment.created_at.desc()).all()

    def update_status(self, payment_id: int, status: PaymentStatus) -> Optional[Payment]:
        """Обновляет статус платежа"""
        payment = self.get_by_id(payment_id)
        if payment:
            payment.status = status
            self.db.flush()
            self.db.refresh(payment)
        return payment

    def get_by_external_id(self, external_payment_id: str) -> Optional[Payment]:
        """Получает платеж по внешнему ID"""
        return self.db.query(Payment).filter(
            Payment.external_payment_id == external_payment_id
        ).first()

    def get_pending_payments(self) -> List[Payment]:
        """Получает все платежи в ожидании"""
        return self.db.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING
        ).all()

    def get_payments_by_status(self, status: PaymentStatus) -> List[Payment]:
        """Получает платежи по статусу"""
        return self.db.query(Payment).filter(
            Payment.status == status
        ).all() 