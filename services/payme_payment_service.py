from sqlalchemy.orm import Session
from typing import List, Dict
from models.payment import Payment, PaymentStatus, PaymentType
from models.user import User
from models.payme_payment import PaymeCardToken
from repositories.payment_repository import PaymentRepository
from repositories.subscription_repository import SubscriptionRepository

from services.payme_subscribe_service import PaymeSubscribeService
from services.toy_box_service import ToyBoxService
from utils.currency import sums_to_tiyin, tiyin_to_sums
import logging


class PaymePaymentService:
    """Сервис для работы с Payme платежами"""

    def __init__(self, db: Session):
        self.db = db
        self.payme_subscribe = PaymeSubscribeService()
        self.payment_repo = PaymentRepository(db)
        self.subscription_repo = SubscriptionRepository(db)

        self.toy_box_service = ToyBoxService(db)

    async def save_card_token(self, user_id: int, token: str, card_number: str, expire_date: str) -> Dict:
        """Сохранить токен карты в отдельной таблице"""
        try:
            # Проверить существование пользователя
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error_message": "Пользователь не найден"
                }

            # Создать новый токен карты
            card_token = PaymeCardToken(
                user_id=user_id,
                card_token=token,
                card_number=card_number,
                expire_date=expire_date,
                is_verified=True  # предполагаем что токен уже верифицирован
            )
            
            self.db.add(card_token)
            self.db.flush()  # Нужен ID для ответа
            self.db.refresh(card_token)

            return {
                "success": True,
                "token_id": card_token.id
            }

        except Exception as e:
            logging.error(f"Error saving card token: {e}")
            return {
                "success": False,
                "error_message": "Ошибка сохранения токена"
            }

    async def charge_subscription(self, user_id: int, subscription_ids: List[int], description: str = "") -> Dict:
        """Списать деньги за подписки по сохраненному токену"""
        try:
            # Получить пользователя и его активный токен
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error_message": "Пользователь не найден"
                }

            # Получить активный токен карты пользователя
            card_token = self.db.query(PaymeCardToken).filter(
                PaymeCardToken.user_id == user_id,
                PaymeCardToken.is_deleted == False,
                PaymeCardToken.is_verified == True
            ).order_by(PaymeCardToken.created_at.desc()).first()
            if not card_token:
                return {
                    "success": False,
                    "error_message": "Активный токен карты не найден"
                }

            # Получить подписки и рассчитать сумму
            subscriptions = self.subscription_repo.get_by_ids(subscription_ids)
            if not subscriptions:
                return {
                    "success": False,
                    "error_message": "Подписки не найдены"
                }

            total_amount = sum(sums_to_tiyin(sub.individual_price) for sub in subscriptions)

            # Создать чек
            receipt_result = await self.payme_subscribe.create_receipt(
                amount=total_amount,
                account={"id": str(user_id)},
                description=description or "Подписка на Box4Kids",
                detail={
                    "receipt_type": 0,
                    "items": [{
                        "discount": 0,
                        "title": "Подписка на Box4Kids",
                        "price": total_amount,
                        "count": 1,
                        "code": "00702001001000001",
                        "units": 241092,
                        "vat_percent": 15,
                        "package_code": "123456"
                    }]
                }
            )

            receipt_id = receipt_result["receipt"]["_id"]

            # Списать деньги
            pay_result = await self.payme_subscribe.pay_receipt(receipt_id, card_token.card_token)

            # Создать универсальную запись платежа
            payment = Payment(
                user_id=user_id,
                amount=tiyin_to_sums(total_amount),
                currency="UZS",
                status=PaymentStatus.COMPLETED,
                payment_type=PaymentType.PAYME,
                external_payment_id=receipt_id,
                payme_receipt_id=receipt_id,
                payme_card_token_id=card_token.id
            )
            payment = self.payment_repo.create(payment)

            # Привязать платеж к подпискам
            for subscription in subscriptions:
                subscription.payment_id = payment.id

                # Создать ToyBox
                try:
                    toy_box = self.toy_box_service.create_box_for_subscription(subscription.id)
                    logging.info(f"Created ToyBox {toy_box.id} for subscription {subscription.id}")
                except Exception as e:
                    logging.error(f"Failed to create ToyBox for subscription {subscription.id}: {e}")

            return {
                "success": True,
                "receipt_id": receipt_id,
                "status": pay_result,
                "payment_id": payment.id
            }

        except Exception as e:
            logging.error(f"Error charging subscription: {e}")
            return {
                "success": False,
                "error_message": "Ошибка списания средств"
            }
