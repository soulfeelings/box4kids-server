from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from models.click_payment import ClickPayment, ClickCardToken, ClickPaymentStatus
from models.subscription import Subscription
from repositories.click_payment_repository import ClickPaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from services.click_merchant_service import ClickMerchantService
from utils.merchant_trans_id import create_merchant_trans_id
import json
import logging


class ClickPaymentService:
    """Сервис для работы с Click платежами"""

    def __init__(self, db: Session):
        self.db = db
        self.click_merchant = ClickMerchantService()
        self.click_payment_repo = ClickPaymentRepository(db)
        self.subscription_repo = SubscriptionRepository(db)

    async def create_card_token(self, user_id: int, card_number: str, expire_date: str) -> Dict:
        """Создать токен карты"""
        try:
            # Вызов Click API
            result = await self.click_merchant.create_card_token(card_number, expire_date)

            if result["error_code"] != 0:
                return {
                    "success": False,
                    "error_message": result["error_note"]
                }

            # Сохранить в БД
            card_token = ClickCardToken(
                user_id=user_id,
                card_token=result["card_token"],
                card_number=card_number,
                expire_date=expire_date,
                is_verified=False
            )
            card_token = self.click_payment_repo.create_card_token(card_token)

            return {
                "success": True,
                "card_token_id": card_token.id,
                "phone_number": result.get("phone_number")
            }

        except Exception as e:
            logging.error(f"Error creating card token: {e}")
            return {
                "success": False,
                "error_message": "Ошибка создания токена карты"
            }

    async def verify_card_token(self, card_token_id: int, sms_code: str) -> Dict:
        """Верифицировать токен карты"""
        try:
            # Получить токен из БД
            card_token = self.click_payment_repo.get_card_token_by_id(card_token_id)

            if not card_token:
                return {
                    "success": False,
                    "error_message": "Токен карты не найден"
                }

            # Вызов Click API
            result = await self.click_merchant.verify_card_token(card_token.card_token, sms_code)

            if result["error_code"] != 0:
                return {
                    "success": False,
                    "error_message": result["error_note"]
                }

            # Обновить статус в БД
            card_token.is_verified = True
            self.db.commit()

            return {"success": True}

        except Exception as e:
            logging.error(f"Error verifying card token: {e}")
            return {
                "success": False,
                "error_message": "Ошибка верификации токена"
            }

    async def initiate_payment(self, user_id: int, subscription_ids: List[int], card_token_id: int) -> Dict:
        """Инициировать платеж по подпискам"""
        try:
            # Проверить токен карты
            card_token = self.db.query(ClickCardToken).filter(
                ClickCardToken.id == card_token_id,
                ClickCardToken.user_id == user_id,
                ClickCardToken.is_verified == True,
                ClickCardToken.is_deleted == False
            ).first()

            if not card_token:
                return {
                    "success": False,
                    "error_message": "Верифицированный токен карты не найден"
                }

            # Получить подписки и рассчитать сумму
            subscriptions = self.subscription_repo.get_by_ids(subscription_ids)
            if not subscriptions:
                return {
                    "success": False,
                    "error_message": "Подписки не найдены"
                }

            # Проверить что все подписки принадлежат пользователю
            for subscription in subscriptions:
                if subscription.child.parent_id != user_id:
                    return {
                        "success": False,
                        "error_message": "Нет доступа к подписке"
                    }

            total_amount = sum(int(sub.individual_price * 100) for sub in subscriptions)  # в тийинах
            merchant_trans_id = create_merchant_trans_id("subscription", user_id, subscription_ids)

            # Создать запись платежа
            click_payment = ClickPayment(
                user_id=user_id,
                card_token_id=card_token_id,
                subscription_ids=json.dumps(subscription_ids),
                amount=total_amount,
                merchant_trans_id=merchant_trans_id,
                status=ClickPaymentStatus.PENDING
            )
            click_payment = self.click_payment_repo.create(click_payment)

            # Вызов Click API для оплаты
            result = await self.click_merchant.payment_with_token(
                card_token.card_token,
                total_amount,
                merchant_trans_id
            )

            if result["error_code"] != 0:
                click_payment.status = ClickPaymentStatus.FAILED
                click_payment.error_code = result["error_code"]
                click_payment.error_note = result["error_note"]
                self.db.commit()

                return {
                    "success": False,
                    "error_message": result["error_note"]
                }

            # Обновить данные платежа
            click_payment.click_payment_id = result.get("payment_id")
            self.db.commit()

            return {
                "success": True,
                "payment_id": click_payment.id,
                "click_payment_id": result.get("payment_id"),
                "status": "pending"
            }

        except Exception as e:
            logging.error(f"Error initiating payment: {e}")
            return {
                "success": False,
                "error_message": "Ошибка инициации платежа"
            }

    def get_payment_status(self, payment_id: int, user_id: int) -> Optional[Dict]:
        """Получить статус платежа"""
        payment = self.db.query(ClickPayment).filter(
            ClickPayment.id == payment_id,
            ClickPayment.user_id == user_id
        ).first()

        if not payment:
            return None

        return {
            "payment_id": payment.id,
            "status": payment.status.value,
            "amount": payment.amount,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat(),
            "error_message": payment.error_note
        }

    def get_user_card_tokens(self, user_id: int) -> List[Dict]:
        """Получить список токенов карт пользователя"""
        tokens = self.click_payment_repo.get_user_card_tokens(user_id)
        return [
            {
                "id": token.id,
                "card_number": token.card_number,
                "expire_date": token.expire_date,
                "is_verified": token.is_verified,
                "created_at": token.created_at.isoformat()
            }
            for token in tokens
        ]
