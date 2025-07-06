from sqlalchemy.orm import Session
from repositories.payment_repository import PaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from services.mock_payment_gateway import MockPaymentGateway
from models.payment import Payment, PaymentStatus
from typing import List, Optional, Dict


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.subscription_repo = SubscriptionRepository(db)
        self.gateway = MockPaymentGateway()  # В продакшне будет RealPaymentGateway

    def create_payment(self, user_id: int, amount: float, currency: str = "RUB") -> Dict:
        """Создает платеж и возвращает данные для оплаты"""
        
        # Вызываем внешний API для создания платежа
        gateway_response = self.gateway.create_payment(
            amount=amount,
            currency=currency,
            return_url=f"https://oursite.com/payment/return",
            notification_url=f"https://oursite.com/payment/webhook"
        )
        
        # Сохраняем платеж в нашей БД
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            external_payment_id=gateway_response["id"]
        )
        
        payment = self.payment_repo.create(payment)
        
        # Возвращаем данные для фронтенда
        return {
            "payment_id": payment.id,
            "external_payment_id": gateway_response["id"],
            "payment_url": gateway_response["payment_url"],
            "amount": amount,
            "currency": currency,
            "expires_at": gateway_response["expires_at"],
            "status": "pending"
        }

    def create_batch_payment(self, subscription_ids: List[int]) -> Dict:
        """Создает пакетный платеж для нескольких подписок"""
        
        # Получаем подписки
        subscriptions = []
        for subscription_id in subscription_ids:
            subscription = self.subscription_repo.get_by_id(subscription_id)
            if not subscription:
                raise ValueError(f"Подписка с ID {subscription_id} не найдена")
            if subscription.payment_id:
                raise ValueError(f"Подписка с ID {subscription_id} уже привязана к платежу")
            subscriptions.append(subscription)
        
        # Проверяем что все подписки принадлежат одному пользователю
        user_ids = set(sub.child.parent_id for sub in subscriptions)
        if len(user_ids) > 1:
            raise ValueError("Все подписки должны принадлежать одному пользователю")
        
        user_id = user_ids.pop()
        
        # Рассчитываем общую сумму
        total_amount = sum(sub.individual_price for sub in subscriptions)
        
        # Создаем платеж
        payment_response = self.create_payment(user_id, total_amount)
        payment_id = payment_response["payment_id"]
        
        # Привязываем подписки к платежу
        for subscription in subscriptions:
            subscription.payment_id = payment_id
            self.db.flush()
        
        payment_response["subscription_count"] = len(subscriptions)
        return payment_response

    async def process_payment_async(self, payment_id: int, simulate_delay: bool = True) -> bool:
        """Асинхронная обработка платежа через внешний API"""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            return False
        
        if payment.status != PaymentStatus.PENDING:
            return False
        
        # Вызываем внешний API для обработки
        gateway_response = await self.gateway.process_payment_async(
            payment.external_payment_id, simulate_delay
        )
        
        # Обновляем статус в нашей БД
        success = gateway_response["status"] == "succeeded"
        new_status = PaymentStatus.COMPLETED if success else PaymentStatus.FAILED
        self.payment_repo.update_status(payment_id, new_status)
        
        return success

    def process_payment(self, payment_id: int) -> bool:
        """Синхронная обработка платежа"""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            return False
        
        if payment.status != PaymentStatus.PENDING:
            return False
        
        # Вызываем внешний API
        gateway_response = self.gateway.process_payment_sync(payment.external_payment_id)
        
        # Обновляем статус в БД
        success = gateway_response["status"] == "succeeded"
        new_status = PaymentStatus.COMPLETED if success else PaymentStatus.FAILED
        self.payment_repo.update_status(payment_id, new_status)
        
        return success

    def handle_user_return(self, external_payment_id: str, status: str = "success") -> Dict:
        """Обработка возврата пользователя с платежной страницы"""
        payment = self.payment_repo.get_by_external_id(external_payment_id)
        if not payment:
            return {"error": "Payment not found"}
        
        # Получаем данные от внешнего API
        gateway_response = self.gateway.simulate_user_return(external_payment_id, status)
        
        # Обновляем статус в БД
        if gateway_response["status"] == "succeeded":
            self.payment_repo.update_status(payment.id, PaymentStatus.COMPLETED)
            return {
                "status": "success",
                "payment_id": payment.id,
                "external_payment_id": external_payment_id,
                "message": "Платеж успешно обработан"
            }
        else:
            self.payment_repo.update_status(payment.id, PaymentStatus.FAILED)
            return {
                "status": "failed",
                "payment_id": payment.id,
                "external_payment_id": external_payment_id,
                "message": "Платеж отклонен"
            }

    def handle_webhook(self, external_payment_id: str, status: str) -> bool:
        """Обработка webhook от внешнего платежного API"""
        payment = self.payment_repo.get_by_external_id(external_payment_id)
        if not payment:
            return False
        
        # Маппинг статусов от внешнего API
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

    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """Получает платеж по ID"""
        return self.payment_repo.get_by_id(payment_id)

    def get_payment_by_external_id(self, external_payment_id: str) -> Optional[Payment]:
        """Получает платеж по внешнему ID"""
        return self.payment_repo.get_by_external_id(external_payment_id)

    def get_user_payments(self, user_id: int) -> List[Payment]:
        """Получает все платежи пользователя"""
        return self.payment_repo.get_by_user_id(user_id)

    def refund_payment(self, payment_id: int) -> bool:
        """Возвращает платеж через внешний API"""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment or payment.status != PaymentStatus.COMPLETED:
            return False
        
        # Вызываем внешний API для возврата
        gateway_response = self.gateway.refund_payment(
            payment.external_payment_id, 
            payment.amount
        )
        
        if gateway_response["status"] == "succeeded":
            self.payment_repo.update_status(payment_id, PaymentStatus.REFUNDED)
            return True
        
        return False


# Для обратной совместимости
MockPaymentService = PaymentService 