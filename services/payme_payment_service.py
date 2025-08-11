from sqlalchemy.orm import Session
from typing import List, Dict
from models.payment import Payment, PaymentStatus
from models.user import User
from repositories.payment_repository import PaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from services.payme_subscribe_service import PaymeSubscribeService
from services.toy_box_service import ToyBoxService
import logging


class PaymePaymentService:
    """Сервис для работы с Payme платежами"""

    def __init__(self, db: Session):
        self.db = db
        self.payme_subscribe = PaymeSubscribeService()
        self.payment_repo = PaymentRepository(db)
        self.subscription_repo = SubscriptionRepository(db)
        self.toy_box_service = ToyBoxService(db)

    async def save_card_token(self, user_id: int, token: str) -> Dict:
        """Сохранить токен карты в профиле пользователя"""
        try:
            # Обновить токен в профиле пользователя
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error_message": "Пользователь не найден"
                }

            user.payme_card_token = token
            self.db.commit()

            return {"success": True}

        except Exception as e:
            logging.error(f"Error saving card token: {e}")
            return {
                "success": False,
                "error_message": "Ошибка сохранения токена"
            }

    async def charge_subscription(self, user_id: int, subscription_ids: List[int], description: str = "") -> Dict:
        """Списать деньги за подписки по сохраненному токену"""
        try:
            # Получить пользователя и его токен
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.payme_card_token:
                return {
                    "success": False,
                    "error_message": "Токен карты не найден"
                }

            # Получить подписки и рассчитать сумму
            subscriptions = self.subscription_repo.get_by_ids(subscription_ids)
            if not subscriptions:
                return {
                    "success": False,
                    "error_message": "Подписки не найдены"
                }

            total_amount = sum(int(sub.individual_price * 100) for sub in subscriptions)  # в тийинах

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
            pay_result = await self.payme_subscribe.pay_receipt(receipt_id, user.payme_card_token)

            # Создать запись платежа в БД
            payment = Payment(
                user_id=user_id,
                amount=total_amount / 100,  # обратно в сумы
                currency="UZS",
                status=PaymentStatus.COMPLETED,
                external_payment_id=receipt_id,
                payme_receipt_id=receipt_id
            )
            payment = self.payment_repo.create(payment)

            # Привязать платеж к подпискам и активировать их
            for subscription in subscriptions:
                subscription.payment_id = payment.id
                subscription.payme_receipt_id = receipt_id

                # Создать ToyBox
                try:
                    toy_box = self.toy_box_service.create_box_for_subscription(subscription.id)
                    logging.info(f"Created ToyBox {toy_box.id} for subscription {subscription.id}")
                except Exception as e:
                    logging.error(f"Failed to create ToyBox for subscription {subscription.id}: {e}")

            self.db.commit()

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
