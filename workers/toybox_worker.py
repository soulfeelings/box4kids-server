import asyncio
import logging
from typing import Dict, Any
from core.messaging import consumer, ToyBoxCreatedEvent, publisher
from core.events import ExchangeNames, QueueNames, RoutingKeys
from core.database import get_db
from services.toy_box_service import ToyBoxService
from services.subscription_service import SubscriptionService


logger = logging.getLogger(__name__)


class ToyBoxWorker:
    """Воркер для обработки событий связанных с ToyBox"""
    
    def __init__(self):
        self.db = next(get_db())
        self.toy_box_service = ToyBoxService(self.db)
        self.subscription_service = SubscriptionService(self.db)
        
        # Регистрируем обработчики событий
        consumer.register_handler(RoutingKeys.PAYMENT_PROCESSED, self.handle_payment_processed)
    
    async def handle_payment_processed(self, event_data: Dict[str, Any]):
        """Обработка события успешной оплаты - создание ToyBox"""
        try:
            user_id = event_data.get('user_id')
            payment_id = event_data.get('payment_id')
            child_id = event_data.get('child_id')
            subscription_id = event_data.get('subscription_id')
            
            # Проверяем типы данных
            if not all([user_id, payment_id, child_id, subscription_id]):
                logger.error("Missing required fields in payment.processed event")
                return
            
            # Type narrowing для линтера
            assert user_id is not None and payment_id is not None and child_id is not None and subscription_id is not None
            
            logger.info(f"Processing payment.processed event for child {child_id}")
            
            # Проверяем что подписка активна
            subscription = self.subscription_service.get_subscription_by_id(int(subscription_id))
            if not subscription:
                logger.error(f"Subscription {subscription_id} not found")
                return
            
            # Проверяем что у ребенка нет активного ToyBox
            existing_box = self.toy_box_service.get_current_box_by_child(int(child_id))
            if existing_box:
                logger.warning(f"Child {child_id} already has active ToyBox {existing_box.id}")
                return
            
            # Создаем первый ToyBox для ребенка
            toy_box = self.toy_box_service.create_box_for_subscription(int(subscription_id))
            
            # Публикуем событие о создании ToyBox
            toybox_event = ToyBoxCreatedEvent(
                toy_box_id=toy_box.id,
                child_id=int(child_id),
                user_id=int(user_id)
            )
            
            publisher.publish_event(
                exchange=ExchangeNames.BOX4KIDS_EVENTS,
                routing_key=toybox_event.get_routing_key(),
                event_data=toybox_event.to_dict()
            )
            
            logger.info(f"Successfully created ToyBox {toy_box.id} for child {child_id}")
            
        except Exception as e:
            logger.error(f"Error processing payment.processed event: {e}")
            raise
    
    async def start_async(self):
        """Асинхронный запуск воркера"""
        logger.info("Starting ToyBox worker (async)...")
        
        try:
            # Настраиваем очередь для этого воркера
            consumer.setup_queue(
                queue_name=QueueNames.TOYBOX,
                exchange=ExchangeNames.BOX4KIDS_EVENTS,
                routing_keys=[RoutingKeys.PAYMENT_PROCESSED]
            )
            
            # Запускаем потребление сообщений в отдельном потоке
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, consumer.start_consuming, QueueNames.TOYBOX)
            
        except asyncio.CancelledError:
            logger.info("ToyBox worker cancelled")
        except Exception as e:
            logger.error(f"ToyBox worker error: {e}")
        finally:
            consumer.close()
            self.db.close()
    
    def start(self):
        """Запуск воркера"""
        logger.info("Starting ToyBox worker...")
        
        try:
            # Настраиваем очередь для этого воркера
            consumer.setup_queue(
                queue_name=QueueNames.TOYBOX,
                exchange=ExchangeNames.BOX4KIDS_EVENTS,
                routing_keys=[RoutingKeys.PAYMENT_PROCESSED]
            )
            
            # Запускаем потребление сообщений
            consumer.start_consuming(QueueNames.TOYBOX)
            
        except KeyboardInterrupt:
            logger.info("ToyBox worker stopped by user")
        except Exception as e:
            logger.error(f"ToyBox worker error: {e}")
        finally:
            consumer.close()
            self.db.close()


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создаем и запускаем воркер
    worker = ToyBoxWorker()
    worker.start() 