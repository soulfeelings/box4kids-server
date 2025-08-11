from sqlalchemy.orm import Session
from typing import Dict
from models.click_payment import ClickPayment, ClickPaymentStatus
from repositories.click_payment_repository import ClickPaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from services.toy_box_service import ToyBoxService
from utils.click_signature import verify_click_signature
from core.config import settings
import json
import logging


class ClickCallbackParams:
    def __init__(self, **kwargs):
        self.click_trans_id = kwargs.get("click_trans_id")
        self.service_id = kwargs.get("service_id")
        self.merchant_trans_id = kwargs.get("merchant_trans_id")
        self.merchant_prepare_id = kwargs.get("merchant_prepare_id")
        self.amount = kwargs.get("amount")
        self.action = kwargs.get("action")
        self.error = kwargs.get("error", 0)
        self.error_note = kwargs.get("error_note", "")
        self.sign_time = kwargs.get("sign_time")
        self.sign_string = kwargs.get("sign_string")


class ClickCallbackService:
    """Сервис для обработки Click callback'ов"""

    def __init__(self, db: Session):
        self.db = db
        self.click_payment_repo = ClickPaymentRepository(db)
        self.subscription_repo = SubscriptionRepository(db)
        self.toy_box_service = ToyBoxService(db)

    def _verify_signature(self, params: ClickCallbackParams) -> bool:
        """Проверить подпись Click callback"""
        if settings.ENVIRONMENT == "development":
            return True

        return verify_click_signature(
            params.click_trans_id,
            params.service_id,
            params.merchant_trans_id,
            params.merchant_prepare_id or "",
            params.amount,
            params.action,
            params.sign_time,
            params.sign_string
        )

    def _create_response(self, params: ClickCallbackParams, error_code: int, error_note: str) -> Dict:
        """Создать ответ для Click"""
        response = {
            "click_trans_id": params.click_trans_id,
            "merchant_trans_id": params.merchant_trans_id,
            "error": error_code,
            "error_note": error_note
        }

        if params.action == 0:  # Prepare
            response["merchant_prepare_id"] = params.merchant_trans_id
        else:  # Complete
            response["merchant_confirm_id"] = params.merchant_trans_id

        return response

    async def handle_callback(self, callback_data: Dict) -> Dict:
        """Обработать Click callback"""
        params = ClickCallbackParams(**callback_data)

        # Проверить подпись
        if not self._verify_signature(params):
            logging.error("Invalid Click signature")
            return self._create_response(params, -1, "Invalid signature")

        try:
            if params.action == 0:
                return await self._handle_prepare(params)
            elif params.action == 1:
                return await self._handle_complete(params)
            else:
                return self._create_response(params, -3, "Invalid action")

        except Exception as e:
            logging.error(f"Click callback error: {e}")
            return self._create_response(params, -8, "System error")

    async def _handle_prepare(self, params: ClickCallbackParams) -> Dict:
        """Обработать Prepare этап"""
        # Найти платеж по merchant_trans_id
        payment = self.click_payment_repo.get_by_merchant_trans_id(params.merchant_trans_id)
        if not payment:
            return self._create_response(params, -5, "Payment not found")

        # Проверить сумму
        if payment.amount != params.amount:
            return self._create_response(params, -2, "Invalid amount")

        # Проверить что платеж еще не завершен
        if payment.status == ClickPaymentStatus.COMPLETED:
            return self._create_response(params, -4, "Payment already completed")

        # Обновить данные платежа
        payment.merchant_prepare_id = params.merchant_trans_id
        payment.click_trans_id = params.click_trans_id
        self.db.commit()

        return self._create_response(params, 0, "Success")

    async def _handle_complete(self, params: ClickCallbackParams) -> Dict:
        """Обработать Complete этап"""
        # Найти платеж по merchant_prepare_id
        payment = self.click_payment_repo.get_by_merchant_prepare_id(params.merchant_prepare_id)

        if not payment:
            return self._create_response(params, -5, "Payment not found")

        # Проверить что платеж еще не завершен
        if payment.status == ClickPaymentStatus.COMPLETED:
            return self._create_response(params, -4, "Payment already completed")

        # Обновить статус платежа
        if params.error == 0:
            payment.status = ClickPaymentStatus.COMPLETED
            payment.error_code = 0
            payment.error_note = "Success"

            # Активировать подписки
            await self._activate_subscriptions(payment)
        else:
            payment.status = ClickPaymentStatus.FAILED
            payment.error_code = params.error
            payment.error_note = params.error_note

        payment.click_trans_id = params.click_trans_id
        self.db.commit()

        return self._create_response(params, 0, "Success")

    async def _activate_subscriptions(self, payment: ClickPayment):
        """Активировать подписки после успешной оплаты"""
        subscription_ids = json.loads(payment.subscription_ids)

        for subscription_id in subscription_ids:
            subscription = self.subscription_repo.get_by_id(subscription_id)
            if subscription:
                # Привязать платеж к подписке
                subscription.click_payment_id = payment.id

                # Создать ToyBox для подписки
                try:
                    toy_box = self.toy_box_service.create_box_for_subscription(subscription_id)
                    logging.info(f"Created ToyBox {toy_box.id} for subscription {subscription_id}")
                except Exception as e:
                    logging.error(f"Failed to create ToyBox for subscription {subscription_id}: {e}")

        self.db.commit()
