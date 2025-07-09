import pika
import json
import logging
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
from core.config import settings
from core.events import ExchangeNames, QueueNames, RoutingKeys, QUEUE_BINDINGS


logger = logging.getLogger(__name__)


class MessagePublisher:
    """Публикатор событий в RabbitMQ"""
    
    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.rabbitmq_url = rabbitmq_url or settings.RABBITMQ_URL
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """Подключение к RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = 'topic'):
        """Объявление exchange"""
        if self.channel is None:
            raise Exception("Channel is not initialized")
        self.channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=True
        )
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """Объявление очереди"""
        if self.channel is None:
            raise Exception("Channel is not initialized")
        self.channel.queue_declare(queue=queue_name, durable=durable)
    
    def publish_event(self, exchange: str, routing_key: str, event_data: Dict[str, Any]):
        """Публикация события"""
        try:
            if not self.connection or self.connection.is_closed:
                self._connect()
            
            if self.channel is None:
                raise Exception("Channel is not initialized")
            
            message = json.dumps(event_data, default=str)
            
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"Published event to {exchange}.{routing_key}: {event_data}")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise
    
    def close(self):
        """Закрытие соединения"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


class MessageConsumer:
    """Потребитель событий из RabbitMQ"""
    
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or settings.RABBITMQ_URL
        self.connection = None
        self.channel = None
        self.handlers: Dict[str, Callable] = {}
        self._connect()
    
    def _connect(self):
        """Подключение к RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            logger.info("Consumer connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def register_handler(self, routing_key: str, handler: Callable):
        """Регистрация обработчика события"""
        self.handlers[routing_key] = handler
    
    def setup_queue(self, queue_name: str, exchange: str, routing_keys: list):
        """Настройка очереди с привязкой к exchange"""
        # Объявляем exchange
        self.channel.exchange_declare(
            exchange=exchange,
            exchange_type='topic',
            durable=True
        )
        
        # Объявляем очередь
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        # Привязываем очередь к exchange
        for routing_key in routing_keys:
            self.channel.queue_bind(
                exchange=exchange,
                queue=queue_name,
                routing_key=routing_key
            )
    
    def _process_message(self, ch, method, properties, body):
        """Обработка сообщения"""
        try:
            message_data = json.loads(body.decode('utf-8'))
            routing_key = method.routing_key
            
            logger.info(f"Processing message {routing_key}: {message_data}")
            
            # Находим обработчик
            handler = self.handlers.get(routing_key)
            if handler:
                handler(message_data)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Message {routing_key} processed successfully")
            else:
                logger.warning(f"No handler for routing key: {routing_key}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self, queue_name: str):
        """Запуск потребления сообщений"""
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=self._process_message
        )
        
        logger.info(f"Starting to consume from queue: {queue_name}")
        self.channel.start_consuming()
    
    def close(self):
        """Закрытие соединения"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


# Базовый класс для событий
class BaseEvent(ABC):
    """Базовый класс для всех событий"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_routing_key(self) -> str:
        pass


# Конкретные события
class PaymentProcessedEvent(BaseEvent):
    """Событие успешной оплаты"""
    
    def __init__(self, user_id: int, payment_id: int, child_id: int, subscription_id: int):
        self.user_id = user_id
        self.payment_id = payment_id
        self.child_id = child_id
        self.subscription_id = subscription_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'payment_id': self.payment_id,
            'child_id': self.child_id,
            'subscription_id': self.subscription_id
        }
    
    def get_routing_key(self) -> str:
        return RoutingKeys.PAYMENT_PROCESSED


class ToyBoxCreatedEvent(BaseEvent):
    """Событие создания набора игрушек"""
    
    def __init__(self, toy_box_id: int, child_id: int, user_id: int):
        self.toy_box_id = toy_box_id
        self.child_id = child_id
        self.user_id = user_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'toy_box_id': self.toy_box_id,
            'child_id': self.child_id,
            'user_id': self.user_id
        }
    
    def get_routing_key(self) -> str:
        return RoutingKeys.TOYBOX_CREATED


# Глобальные экземпляры
publisher = MessagePublisher()
consumer = MessageConsumer()

# Настройка exchange и очередей при инициализации
try:
    publisher.declare_exchange(ExchangeNames.BOX4KIDS_EVENTS, 'topic')
    
    # Автоматическая настройка очередей из конфигурации
    for queue_name, routing_keys in QUEUE_BINDINGS.items():
        if queue_name in [QueueNames.TOYBOX, QueueNames.NOTIFICATIONS]:  # Пока только базовые
            consumer.setup_queue(queue_name, ExchangeNames.BOX4KIDS_EVENTS, routing_keys)
    
except Exception as e:
    logger.error(f"Failed to setup RabbitMQ infrastructure: {e}") 