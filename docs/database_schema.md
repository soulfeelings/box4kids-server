# Схема таблиц которых еще нет или надо обновить в базе данных Box4Kids

## Обзор

Система подписок на развивающие игрушки для детей с персонализацией по возрасту, интересам и навыкам.

## Основные сущности

### 1. SubscriptionPlan - Тарифные планы

Таблица с доступными тарифами подписки.

| Поле          | Тип      | Описание                          |
| ------------- | -------- | --------------------------------- |
| id            | Integer  | Первичный ключ                    |
| name          | String   | Название плана (Базовый, Премиум) |
| price_monthly | Float    | Стоимость в месяц (USD)           |
| toy_count     | Integer  | Количество игрушек в наборе       |
| description   | Text     | Описание плана                    |
| created_at    | DateTime | Дата создания                     |

**Примеры данных:**

- Базовый: $35/мес, 6 игрушек
- Премиум: $60/мес, 9 игрушек

### 2. ToyCategory - Категории игрушек (уже реализован)

Справочник категорий игрушек.

| Поле        | Тип      | Описание           |
| ----------- | -------- | ------------------ |
| id          | Integer  | Первичный ключ     |
| name        | String   | Название категории |
| description | Text     | Описание категории |
| icon        | String   | Иконка для UI      |
| created_at  | DateTime | Дата создания      |

**Примеры данных:**

- Конструктор, Творческий набор, Мягкая игрушка, Головоломка, Премиум-игрушка

### 3. PlanToyConfiguration - Состав планов

Связь между планами и категориями игрушек с указанием количества.

| Поле        | Тип     | Описание                            |
| ----------- | ------- | ----------------------------------- |
| id          | Integer | Первичный ключ                      |
| plan_id     | Integer | FK на SubscriptionPlan              |
| category_id | Integer | FK на ToyCategory                   |
| quantity    | Integer | Количество игрушек данной категории |

**Связи:**

- plan_id → SubscriptionPlan.id
- category_id → ToyCategory.id

### 4. Child - Дети (расширение существующей)

Информация о детях пользователей.

| Поле                  | Тип      | Описание                    |
| --------------------- | -------- | --------------------------- |
| id                    | Integer  | Первичный ключ              |
| name                  | String   | Имя ребенка                 |
| date_of_birth         | Date     | Дата рождения               |
| gender                | Enum     | Пол (male/female)           |
| parent_id             | Integer  | FK на User                  |
| has_limitations       | Boolean  | Есть ли особенности         |
| special_needs_comment | Text     | Комментарий об особенностях |
| created_at            | DateTime | Дата создания               |

**Связи:**

- parent_id → User.id

### 5. Subscription - Подписки

Активные подписки детей на планы.

| Поле             | Тип      | Описание                         |
| ---------------- | -------- | -------------------------------- |
| id               | Integer  | Первичный ключ                   |
| child_id         | Integer  | FK на Child                      |
| plan_id          | Integer  | FK на SubscriptionPlan           |
| status           | Enum     | Статус (active/paused/cancelled) |
| discount_percent | Float    | Процент скидки                   |
| created_at       | DateTime | Дата создания                    |
| expires_at       | DateTime | Дата окончания                   |

**Связи:**

- child_id → Child.id
- plan_id → SubscriptionPlan.id

**Статусы:**

- active - активная подписка
- paused - приостановлена
- cancelled - отменена

### 9. BoxReview - Отзывы на коробки

Оценки и отзывы пользователей на полученные коробки.

| Поле       | Тип      | Описание              |
| ---------- | -------- | --------------------- |
| id         | Integer  | Первичный ключ        |
| box_id     | Integer  | FK на SubscriptionBox |
| rating     | Integer  | Оценка (1-5 звезд)    |
| comment    | Text     | Текст отзыва          |
| created_at | DateTime | Дата создания         |

**Связи:**

- box_id → SubscriptionBox.id

### 10. DeliveryInfo - Информация о доставке

Адреса и предпочтения доставки пользователей.

| Поле                     | Тип      | Описание                        |
| ------------------------ | -------- | ------------------------------- |
| id                       | Integer  | Первичный ключ                  |
| user_id                  | Integer  | FK на User                      |
| address                  | String   | Адрес доставки                  |
| delivery_time_preference | String   | Предпочтительное время доставки |
| courier_comment          | Text     | Комментарий для курьера         |
| created_at               | DateTime | Дата создания                   |

**Связи:**

- user_id → User.id

## Существующие таблицы

### User - Пользователи (существующая)

- Основная информация о пользователях
- Связи: children, subscriptions, delivery_info, payments

### Interest - Интересы детей (существующая)

- Справочник интересов
- Many-to-many связь с Child через child_interests

### Skill - Навыки детей (существующая)

- Справочник навыков для развития
- Many-to-many связь с Child через child_skills

### Payment - Платежи (существующая)

- История платежей за подписки
- Связь с User и Subscription

## Бизнес-логика

### Скидки

- Скидка 20% на подписку для второго ребенка
- Рассчитывается автоматически при создании подписки

### Персонализация

- Игрушки подбираются на основе:
  - Возраста ребенка
  - Выбранных интересов
  - Навыков для развития
  - Особенностей ребенка

### Доставка

- Ежемесячная доставка коробок
- Отслеживание статуса каждой коробки
- История всех доставок

## Индексы

Рекомендуемые индексы для оптимизации производительности:

```sql
-- Подписки пользователя
CREATE INDEX idx_subscription_child_id ON subscriptions(child_id);
CREATE INDEX idx_subscription_status ON subscriptions(status);

-- Коробки подписки
CREATE INDEX idx_box_subscription_id ON subscription_boxes(subscription_id);
CREATE INDEX idx_box_status ON subscription_boxes(status);

-- Игрушки в коробке
CREATE INDEX idx_box_toy_box_id ON box_toys(box_id);
CREATE INDEX idx_box_toy_toy_id ON box_toys(toy_id);

-- Отзывы
CREATE INDEX idx_review_box_id ON box_reviews(box_id);
```

## Примеры использования

### Создание подписки с скидкой

```sql
-- Если у пользователя уже есть активная подписка,
-- новая подписка получает скидку 20%
INSERT INTO subscriptions (child_id, plan_id, status, discount_percent)
VALUES (2, 1, 'active', 20.0);
```

### Получение текущей коробки ребенка

```sql
SELECT sb.*, s.plan_id, sp.name as plan_name
FROM subscription_boxes sb
JOIN subscriptions s ON sb.subscription_id = s.id
JOIN subscription_plans sp ON s.plan_id = sp.id
WHERE s.child_id = 1 AND sb.status = 'packaging'
ORDER BY sb.created_at DESC
LIMIT 1;
```
