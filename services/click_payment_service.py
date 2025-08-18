from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from models.payment import Payment, PaymentStatus, PaymentType
from models.click_payment import ClickCardToken
from repositories.payment_repository import PaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from services.click_merchant_service import ClickMerchantService
from utils.merchant_trans_id import create_merchant_trans_id
from utils.currency import sums_to_tiyin, tiyin_to_sums
import logging


class ClickPaymentService:
    """Сервис для работы с Click платежами"""

    def __init__(self, db: Session):
        self.db = db
        self.click_merchant = ClickMerchantService()
        self.payment_repo = PaymentRepository(db)
        self.subscription_repo = SubscriptionRepository(db)

    async def create_card_token(self, user_id: int, card_number: str, expire_date: str) -> Dict:
        """Создать токен карты"""
        logging.info(f"🔵 [CLICK] Creating card token for user {user_id}, card ending: ***{card_number[-4:]}")
        
        try:
            # Вызов Click API
            logging.info(f"🔵 [CLICK] Calling Click API to create card token")
            result = await self.click_merchant.create_card_token(card_number, expire_date)
            logging.info(f"🔵 [CLICK] Click API response: error_code={result.get('error_code')}, has_token={bool(result.get('card_token'))}")

            if result["error_code"] != 0:
                logging.warning(f"🔵 [CLICK] Card token creation failed: {result['error_note']}")
                return {
                    "success": False,
                    "error_message": result["error_note"]
                }

            # Сохранить в БД
            logging.info(f"🔵 [CLICK] Saving card token to database")
            card_token = ClickCardToken(
                user_id=user_id,
                card_token=result["card_token"],
                card_number=card_number,
                expire_date=expire_date,
                is_verified=False
            )
            self.db.add(card_token)
            self.db.flush()
            self.db.refresh(card_token)
            
            logging.info(f"🔵 [CLICK] Card token created successfully: ID={card_token.id}")

            return {
                "success": True,
                "card_token_id": card_token.id,
                "phone_number": result.get("phone_number")
            }

        except Exception as e:
            logging.error(f"🔴 [CLICK] Error creating card token: {e}", exc_info=True)
            return {
                "success": False,
                "error_message": "Ошибка создания токена карты"
            }

    async def verify_card_token(self, card_token_id: int, sms_code: str) -> Dict:
        """Верифицировать токен карты"""
        logging.info(f"🔵 [CLICK] Verifying card token: ID={card_token_id}, SMS code={sms_code}")
        
        try:
            # Получить токен из БД
            logging.info(f"🔵 [CLICK] Looking up card token in database: ID={card_token_id}")
            card_token = self.db.query(ClickCardToken).filter(
                ClickCardToken.id == card_token_id,
                ClickCardToken.is_deleted == False
            ).first()

            if not card_token:
                logging.warning(f"🔵 [CLICK] Card token not found: ID={card_token_id}")
                return {
                    "success": False,
                    "error_message": "Токен карты не найден"
                }

            logging.info(f"🔵 [CLICK] Found card token: ID={card_token.id}, verified={card_token.is_verified}")

            # Вызов Click API
            logging.info(f"🔵 [CLICK] Calling Click API to verify token with SMS code")
            result = await self.click_merchant.verify_card_token(card_token.card_token, sms_code)
            logging.info(f"🔵 [CLICK] Click API verification response: error_code={result.get('error_code')}")

            if result["error_code"] != 0:
                logging.warning(f"🔵 [CLICK] Card token verification failed: {result['error_note']}")
                return {
                    "success": False,
                    "error_message": result["error_note"]
                }

            # Обновить статус в БД
            logging.info(f"🔵 [CLICK] Updating card token verification status")
            card_token.is_verified = True
            
            logging.info(f"🔵 [CLICK] Card token verified successfully: ID={card_token_id}")
            return {"success": True}

        except Exception as e:
            logging.error(f"🔴 [CLICK] Error verifying card token: {e}", exc_info=True)
            return {
                "success": False,
                "error_message": "Ошибка верификации токена"
            }

    async def initiate_payment(self, user_id: int, subscription_ids: List[int], card_token_id: int) -> Dict:
        """Инициировать платеж по подпискам"""
        logging.info(f"🔵 [CLICK] Initiating payment: user_id={user_id}, subscriptions={subscription_ids}, card_token_id={card_token_id}")
        
        try:
            # Проверить токен карты
            logging.info(f"🔵 [CLICK] Looking up verified card token: ID={card_token_id}, user_id={user_id}")
            card_token = self.db.query(ClickCardToken).filter(
                ClickCardToken.id == card_token_id,
                ClickCardToken.user_id == user_id,
                ClickCardToken.is_verified == True,
                ClickCardToken.is_deleted == False
            ).first()

            if not card_token:
                logging.warning(f"🔵 [CLICK] Verified card token not found: ID={card_token_id}, user_id={user_id}")
                return {
                    "success": False,
                    "error_message": "Верифицированный токен карты не найден"
                }

            logging.info(f"🔵 [CLICK] Found verified card token: ID={card_token.id}")

            # Получить подписки и рассчитать сумму
            logging.info(f"🔵 [CLICK] Looking up subscriptions: {subscription_ids}")
            subscriptions = self.subscription_repo.get_by_ids(subscription_ids)
            if not subscriptions:
                logging.warning(f"🔵 [CLICK] Subscriptions not found: {subscription_ids}")
                return {
                    "success": False,
                    "error_message": "Подписки не найдены"
                }
            
            logging.info(f"🔵 [CLICK] Found {len(subscriptions)} subscriptions")

            # Проверить что все подписки принадлежат пользователю
            logging.info(f"🔵 [CLICK] Checking subscription ownership for user {user_id}")
            for subscription in subscriptions:
                if subscription.child.parent_id != user_id:
                    logging.warning(f"🔵 [CLICK] Access denied to subscription {subscription.id} for user {user_id}")
                    return {
                        "success": False,
                        "error_message": "Нет доступа к подписке"
                    }

            total_amount = sum(sums_to_tiyin(sub.individual_price) for sub in subscriptions)
            logging.info(f"🔵 [CLICK] Calculated total amount: {total_amount} tiyin ({tiyin_to_sums(total_amount)} sums)")
            
            merchant_trans_id = create_merchant_trans_id("subscription", user_id, subscription_ids)
            logging.info(f"🔵 [CLICK] Generated merchant_trans_id: {merchant_trans_id}")

            # Создать запись платежа
            logging.info(f"🔵 [CLICK] Creating payment record in database")
            payment = Payment(
                user_id=user_id,
                amount=tiyin_to_sums(total_amount),
                currency="UZS",
                status=PaymentStatus.PENDING,
                payment_type=PaymentType.CLICK,
                merchant_trans_id=merchant_trans_id,
                click_card_token_id=card_token_id
            )
            payment = self.payment_repo.create(payment)
            logging.info(f"🔵 [CLICK] Payment record created: ID={payment.id}")

            # Вызов Click API для оплаты
            result = await self.click_merchant.payment_with_token(
                card_token.card_token,
                total_amount,
                merchant_trans_id
            )

            if result["error_code"] != 0:
                payment.status = PaymentStatus.FAILED
                payment.error_code = result["error_code"]
                payment.error_message = result["error_note"]

                return {
                    "success": False,
                    "error_message": result["error_note"]
                }

            # Обновить данные платежа
            payment.external_payment_id = result.get("payment_id")
            payment.click_trans_id = result.get("click_trans_id")
            
            # Привязать подписки к платежу
            for subscription in subscriptions:
                subscription.payment_id = payment.id

            return {
                "success": True,
                "payment_id": payment.id,
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
        payment = self.payment_repo.get_by_id(payment_id)
        
        if not payment or payment.user_id != user_id:
            return None

        return {
            "payment_id": payment.id,
            "status": payment.status.value,
            "amount": payment.amount,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat(),
            "error_message": payment.error_message
        }

    def get_user_card_tokens(self, user_id: int) -> List[Dict]:
        """Получить список токенов карт пользователя"""
        tokens = self.db.query(ClickCardToken).filter(
            ClickCardToken.user_id == user_id,
            ClickCardToken.is_deleted == False
        ).all()
        
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
