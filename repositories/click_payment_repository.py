from sqlalchemy.orm import Session
from models.click_payment import ClickPayment, ClickCardToken
from typing import List, Optional, Dict


class ClickPaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment: ClickPayment) -> ClickPayment:
        """Создать платеж"""
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_by_id(self, payment_id: int) -> Optional[ClickPayment]:
        """Получить платеж по ID"""
        return self.db.query(ClickPayment).filter(ClickPayment.id == payment_id).first()

    def get_by_merchant_trans_id(self, merchant_trans_id: str) -> Optional[ClickPayment]:
        """Получить платеж по merchant_trans_id"""
        return self.db.query(ClickPayment).filter(
            ClickPayment.merchant_trans_id == merchant_trans_id
        ).first()

    def get_by_merchant_prepare_id(self, merchant_prepare_id: str) -> Optional[ClickPayment]:
        """Получить платеж по merchant_prepare_id"""
        return self.db.query(ClickPayment).filter(
            ClickPayment.merchant_prepare_id == merchant_prepare_id
        ).first()

    def update(self, payment_id: int, data: Dict) -> Optional[ClickPayment]:
        """Обновить платеж"""
        payment = self.get_by_id(payment_id)
        if payment:
            for key, value in data.items():
                setattr(payment, key, value)
            self.db.commit()
            self.db.refresh(payment)
        return payment

    def get_user_card_tokens(self, user_id: int) -> List[ClickCardToken]:
        """Получить токены карт пользователя"""
        return self.db.query(ClickCardToken).filter(
            ClickCardToken.user_id == user_id,
            ClickCardToken.is_deleted == False
        ).all()

    def create_card_token(self, card_token: ClickCardToken) -> ClickCardToken:
        """Создать токен карты"""
        self.db.add(card_token)
        self.db.commit()
        self.db.refresh(card_token)
        return card_token

    def get_card_token_by_id(self, token_id: int) -> Optional[ClickCardToken]:
        """Получить токен карты по ID"""
        return self.db.query(ClickCardToken).filter(
            ClickCardToken.id == token_id,
            ClickCardToken.is_deleted == False
        ).first()
