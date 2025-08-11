from sqlalchemy.orm import Session
from typing import Dict, Optional
from models.payment import Payment, PaymentStatus
from repositories.payment_repository import PaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from services.toy_box_service import ToyBoxService
from utils.payme_signature import verify_payme_signature
from utils.currency import validate_amount_match, is_valid_payment_amount, sums_to_tiyin, tiyin_to_sums
from core.config import settings
import json
import logging


class PaymeCallbackParams:
    """Параметры Payme callback"""
    def __init__(self, method: str, params: Dict, request_id: Optional[int] = None):
        self.method = method
        self.params = params
        self.request_id = request_id
        
        # Извлекаем общие параметры
        self.amount = params.get("amount")
        self.account = params.get("account", {})
        self.transaction_id = params.get("id")


class PaymeCallbackService:
    """Сервис для обработки Payme callback'ов"""

    # Коды ошибок Payme
    ERROR_CODES = {
        "INVALID_AMOUNT": -31001,
        "TRANSACTION_NOT_FOUND": -31003,
        "INVALID_ACCOUNT": -31050,
        "UNABLE_TO_PERFORM": -31008,
        "SYSTEM_ERROR": -32400,
    }

    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.subscription_repo = SubscriptionRepository(db)
        self.toy_box_service = ToyBoxService(db)



    def _create_error_response(self, request_id: int, error_code: int, message: str) -> Dict:
        """Создать ответ с ошибкой для Payme"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": error_code,
                "message": message
            }
        }

    def _create_success_response(self, request_id: int, result: Dict) -> Dict:
        """Создать успешный ответ для Payme"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    async def handle_callback(self, signature: str, body: bytes, callback_data: Dict) -> Dict:
        """Обработать Payme callback"""
        
        # Проверить подпись
        if not verify_payme_signature(signature, body):
            logging.error("Invalid Payme signature")
            return self._create_error_response(
                callback_data.get("id", 0),
                self.ERROR_CODES["SYSTEM_ERROR"],
                "Invalid signature"
            )

        params = PaymeCallbackParams(
            method=callback_data.get("method", ""),
            params=callback_data.get("params", {}),
            request_id=callback_data.get("id", 0)
        )

        try:
            if params.method == "CheckPerformTransaction":
                return await self._check_perform_transaction(params)
            elif params.method == "CreateTransaction":
                return await self._create_transaction(params)
            elif params.method == "PerformTransaction":
                return await self._perform_transaction(params)
            elif params.method == "CancelTransaction":
                return await self._cancel_transaction(params)
            elif params.method == "CheckTransaction":
                return await self._check_transaction(params)
            else:
                return self._create_error_response(
                    params.request_id,
                    self.ERROR_CODES["SYSTEM_ERROR"],
                    f"Unknown method: {params.method}"
                )

        except Exception as e:
            logging.error(f"Payme callback error: {e}")
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["SYSTEM_ERROR"],
                "System error"
            )

    async def _check_perform_transaction(self, params: PaymeCallbackParams) -> Dict:
        """Проверить возможность проведения транзакции"""
        
        # Извлекаем данные из account
        account = params.account
        user_id = account.get("user_id")
        subscription_ids = account.get("subscription_ids", [])
        
        if not user_id or not subscription_ids:
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["INVALID_ACCOUNT"],
                "Invalid account data"
            )

        # Получаем подписки и проверяем сумму
        subscriptions = self.subscription_repo.get_by_ids(subscription_ids)
        if not subscriptions:
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["INVALID_ACCOUNT"],
                "Subscriptions not found"
            )

        # Проверяем что все подписки принадлежат пользователю
        for subscription in subscriptions:
            if subscription.child.parent_id != user_id:
                return self._create_error_response(
                    params.request_id,
                    self.ERROR_CODES["INVALID_ACCOUNT"],
                    "Access denied to subscription"
                )

        # Проверяем суммы подписок и конвертируем в тийины
        total_sums = sum(sub.individual_price for sub in subscriptions)
        
        # Проверяем валидность общей суммы
        if not is_valid_payment_amount(total_sums):
            logging.error(f"Invalid total subscription amount: {total_sums}")
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["INVALID_AMOUNT"],
                "Invalid subscription amount"
            )
        
        # Дополнительная проверка на разумность суммы от Payme
        if params.amount <= 0:
            logging.error(f"Invalid amount from Payme: {params.amount}")
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["INVALID_AMOUNT"],
                "Amount must be positive"
            )
        
        # Проверяем соответствие сумм с использованием утилиты
        if not validate_amount_match(total_sums, params.amount):
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["INVALID_AMOUNT"],
                f"Amount mismatch. Expected: {sums_to_tiyin(total_sums)}, got: {params.amount}"
            )

        return self._create_success_response(params.request_id, {"allow": True})

    async def _create_transaction(self, params: PaymeCallbackParams) -> Dict:
        """Создать транзакцию"""
        
        # Проверяем не создана ли уже транзакция с таким ID
        existing_payment = self.payment_repo.get_by_external_id(params.transaction_id)
        if existing_payment:
            if existing_payment.status == PaymentStatus.PENDING:
                return self._create_success_response(params.request_id, {
                    "create_time": int(existing_payment.created_at.timestamp() * 1000),
                    "transaction": params.transaction_id,
                    "state": 1
                })
            else:
                return self._create_error_response(
                    params.request_id,
                    self.ERROR_CODES["UNABLE_TO_PERFORM"],
                    "Transaction already processed"
                )

        # Повторяем проверки из CheckPerformTransaction
        check_result = await self._check_perform_transaction(params)
        if "error" in check_result:
            return check_result

        # Создаем платеж
        account = params.account
        user_id = account.get("user_id")
        subscription_ids = account.get("subscription_ids", [])
        
        payment = Payment(
            user_id=user_id,
            amount=tiyin_to_sums(params.amount),
            currency="UZS",
            status=PaymentStatus.PENDING,
            payment_type="payme",
            external_payment_id=params.transaction_id,
            payme_receipt_id=params.transaction_id
        )
        
        payment = self.payment_repo.create(payment)
        
        # Привязываем подписки к платежу
        subscriptions = self.subscription_repo.get_by_ids(subscription_ids)
        for subscription in subscriptions:
            subscription.payment_id = payment.id

        return self._create_success_response(params.request_id, {
            "create_time": int(payment.created_at.timestamp() * 1000),
            "transaction": params.transaction_id,
            "state": 1
        })

    async def _perform_transaction(self, params: PaymeCallbackParams) -> Dict:
        """Провести транзакцию"""
        
        # Найти платеж
        payment = self.payment_repo.get_by_external_id(params.transaction_id)
        if not payment:
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["TRANSACTION_NOT_FOUND"],
                "Transaction not found"
            )

        # Проверить что транзакция в правильном состоянии
        if payment.status != PaymentStatus.PENDING:
            if payment.status == PaymentStatus.COMPLETED:
                return self._create_success_response(params.request_id, {
                    "perform_time": int(payment.updated_at.timestamp() * 1000),
                    "transaction": params.transaction_id,
                    "state": 2
                })
            else:
                return self._create_error_response(
                    params.request_id,
                    self.ERROR_CODES["UNABLE_TO_PERFORM"],
                    f"Cannot perform transaction in status: {payment.status.value}"
                )

        # Обновить статус платежа
        payment.status = PaymentStatus.COMPLETED
        self.db.flush()

        # Активировать подписки и создать ToyBox'ы
        await self._activate_subscriptions(payment)

        return self._create_success_response(params.request_id, {
            "perform_time": int(payment.updated_at.timestamp() * 1000),
            "transaction": params.transaction_id,
            "state": 2
        })

    async def _cancel_transaction(self, params: PaymeCallbackParams) -> Dict:
        """Отменить транзакцию"""
        
        payment = self.payment_repo.get_by_external_id(params.transaction_id)
        if not payment:
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["TRANSACTION_NOT_FOUND"],
                "Transaction not found"
            )

        # Определяем причину отмены
        reason = params.params.get("reason", 0)
        
        if payment.status == PaymentStatus.PENDING:
            # Транзакция еще не проведена - просто отменяем
            payment.status = PaymentStatus.FAILED
            payment.error_message = f"Cancelled by Payme, reason: {reason}"
        elif payment.status == PaymentStatus.COMPLETED:
            # Транзакция проведена - делаем возврат
            payment.status = PaymentStatus.REFUNDED
            payment.error_message = f"Refunded by Payme, reason: {reason}"
            
            # TODO: Здесь должна быть логика отмены ToyBox'ов и подписок

        return self._create_success_response(params.request_id, {
            "cancel_time": int(payment.updated_at.timestamp() * 1000),
            "transaction": params.transaction_id,
            "state": -1 if payment.status == PaymentStatus.FAILED else -2
        })

    async def _check_transaction(self, params: PaymeCallbackParams) -> Dict:
        """Проверить статус транзакции"""
        
        payment = self.payment_repo.get_by_external_id(params.transaction_id)
        if not payment:
            return self._create_error_response(
                params.request_id,
                self.ERROR_CODES["TRANSACTION_NOT_FOUND"],
                "Transaction not found"
            )

        # Маппинг статусов
        state_mapping = {
            PaymentStatus.PENDING: 1,
            PaymentStatus.COMPLETED: 2,
            PaymentStatus.FAILED: -1,
            PaymentStatus.REFUNDED: -2
        }

        result = {
            "create_time": int(payment.created_at.timestamp() * 1000),
            "transaction": params.transaction_id,
            "state": state_mapping.get(payment.status, 1)
        }

        if payment.status == PaymentStatus.COMPLETED:
            result["perform_time"] = int(payment.updated_at.timestamp() * 1000)
        elif payment.status in [PaymentStatus.FAILED, PaymentStatus.REFUNDED]:
            result["cancel_time"] = int(payment.updated_at.timestamp() * 1000)
            if payment.error_message:
                result["reason"] = payment.error_message

        return self._create_success_response(params.request_id, result)

    async def _activate_subscriptions(self, payment: Payment):
        """Активировать подписки после успешной оплаты"""
        
        # Получаем подписки, привязанные к этому платежу
        subscriptions = self.subscription_repo.get_by_payment_id(payment.id)

        for subscription in subscriptions:
            # Создать ToyBox для подписки
            try:
                toy_box = self.toy_box_service.create_box_for_subscription(subscription.id)
                logging.info(f"Created ToyBox {toy_box.id} for subscription {subscription.id}")
            except Exception as e:
                logging.error(f"Failed to create ToyBox for subscription {subscription.id}: {e}")
                # В будущем здесь будет rollback логика
