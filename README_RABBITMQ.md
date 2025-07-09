# Box4Kids + RabbitMQ Integration

## 🚀 Запуск системы

### 1. Для разработки (упрощенно)

```bash
# Запуск всех сервисов для разработки
docker-compose up -d

# Просмотр логов
docker-compose logs -f api
```

**Доступ:**

- **API**: http://localhost:8000
- **RabbitMQ Management**: http://localhost:15672 (**guest/guest** - без пароля!)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 2. Для продакшена (безопасно)

```bash
# Создайте файл с переменными окружения
cp environment.prod.example .env.prod
# Заполните реальными паролями в .env.prod

# Запуск для продакшена
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

**Особенности продакшена:**

- ✅ Безопасные пароли из переменных окружения
- ✅ RabbitMQ Management UI НЕ доступен извне
- ✅ Все сервисы в изолированной сети

### 3. Автоматический запуск воркера

Воркер ToyBox теперь **автоматически запускается** вместе с API сервером через FastAPI `lifespan`:

- При старте API → запускается ToyBox воркер
- При остановке API → воркер корректно завершается

## 🔄 Event-driven поток

### Успешная оплата → Создание ToyBox

1. **Пользователь** завершает оплату
2. **PaymentService** обрабатывает платеж
3. **Публикует событие** `payment.processed` в RabbitMQ
4. **ToyBoxWorker** автоматически получает событие
5. **Создает ToyBox** для ребенка
6. **Публикует событие** `toybox.created` для уведомлений

### Пример события

```json
{
  "user_id": 123,
  "payment_id": 456,
  "child_id": 789,
  "subscription_id": 101
}
```

## 📊 Мониторинг

### RabbitMQ Management UI

- Очереди: `toybox_queue`, `notifications_queue`
- Exchange: `box4kids_events`
- Routing keys: `payment.processed`, `toybox.created`

### Логи сервера

```bash
# Просмотр логов API + воркера
docker-compose logs -f api

# Поиск по логам
docker-compose logs api | grep "ToyBox worker"
```

## 🛠️ Для разработки

### Локальный запуск (без Docker)

```bash
# 1. Запуск только инфраструктуры
docker-compose up -d postgres redis rabbitmq

# 2. Запуск API сервера (воркер запустится автоматически)
python main.py

# 3. Установка зависимостей
pip install pika==1.3.2
```

### Отладка воркера

```bash
# Запуск только воркера (для отладки)
python start_worker.py toybox
```

## 📈 Расширяемость

### Добавление новых воркеров

1. Создать файл `workers/notification_worker.py`
2. Добавить в `main.py` lifespan функцию
3. Зарегистрировать новые routing keys

### Новые события

```python
# В core/messaging.py
class NotificationSentEvent(BaseEvent):
    def get_routing_key(self) -> str:
        return 'notification.sent'

# В воркере
consumer.register_handler('notification.sent', handle_notification)
```

## 🔧 Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PaymentService │    │    RabbitMQ     │    │  ToyBoxWorker   │
│                 │    │                 │    │                 │
│  ✓ Оплата       │───▶│  payment.       │───▶│  Создает        │
│  ✓ Событие      │    │  processed      │    │  ToyBox         │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         │                                              ▼
         │                                   ┌─────────────────┐
         │                                   │NotificationWorker│
         │                                   │                 │
         └────────────────────────────────▶  │  Отправляет     │
                                             │  уведомления    │
                                             │                 │
                                             └─────────────────┘
```

## ✅ Тестирование

### Проверка работы системы

1. Создать пользователя через API
2. Создать подписку
3. Обработать платеж
4. Проверить создание ToyBox
5. Проверить логи воркера

### Пример API вызовов

```bash
# Создание платежа
curl -X POST "http://localhost:8000/payments/batch" \
  -H "Content-Type: application/json" \
  -d '{"subscription_ids": [1]}'

# Обработка платежа
curl -X POST "http://localhost:8000/payments/1/process"
```

## 🎯 Результат

✅ **Развязка сервисов** - PaymentService не знает о ToyBoxService  
✅ **Надежность** - события сохраняются в RabbitMQ  
✅ **Масштабируемость** - можно добавить больше воркеров  
✅ **Мониторинг** - веб-интерфейс RabbitMQ  
✅ **Автоматизация** - воркер запускается с сервером
