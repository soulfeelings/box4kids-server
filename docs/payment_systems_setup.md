# Настройка платежных систем Click и Payme

## Обзор

Реализована интеграция с платежными системами Click и Payme для оплаты подписок Box4Kids.

## Новые компоненты

### Модели

- `ClickCardToken` - токены карт Click
- `ClickPayment` - платежи через Click
- Расширены `Payment`, `User`, `Subscription` для интеграции

### Сервисы

- `ClickMerchantService` - HTTP клиент для Click API
- `PaymeSubscribeService` - JSON-RPC клиент для Payme
- `ClickPaymentService` - бизнес-логика Click платежей
- `PaymePaymentService` - бизнес-логика Payme платежей
- `ClickCallbackService` - обработка Click callbacks

### API Endpoints

#### Click

- `POST /click/card-token/create` - создание токена карты
- `POST /click/card-token/verify` - верификация SMS кодом
- `GET /click/card-tokens` - список токенов пользователя
- `POST /click/payment/initiate` - инициация платежа
- `GET /click/payment/status/{id}` - статус платежа

#### Payme

- `POST /payme/card-token/save` - сохранение токена
- `POST /payme/charge` - списание средств

#### Callbacks

- `POST /payment/callback/click` - Click webhooks
- `POST /payment/callback/payme` - Payme webhooks

## Запуск

### Development

```bash
# 1. Создать .env файл на основе .env.example
# 2. Заполнить тестовые данные для Click/Payme
make dev-up
```

### Production

```bash
# 1. Создать .env.production на основе .env.production.example
# 2. Заполнить production данные для Click/Payme
make prod-up
```

## Переменные окружения

### Обязательные для Click

- `CLICK_MERCHANT_ID`
- `CLICK_SECRET_KEY`
- `CLICK_SERVICE_ID`
- `CLICK_MERCHANT_USER_ID`

### Обязательные для Payme

- `PAYME_MERCHANT_ID`
- `PAYME_SECRET_KEY`

## Workflow платежей

### Click

1. Создание токена карты → SMS верификация
2. Инициация платежа по токену
3. Обработка Prepare/Complete callbacks
4. Автоактивация подписок

### Payme

1. Создание и верификация токена на фронте
2. Сохранение токена в профиле
3. Списание средств по токену
4. Автоактивация подписок

## Безопасность

- Проверка подписей всех callbacks
- Валидация сумм и пользователей
- Защита от повторных платежей
- Soft delete для токенов карт
