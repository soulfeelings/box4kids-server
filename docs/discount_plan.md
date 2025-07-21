# План внедрения системы скидок

## Бизнес-логика

### Правила скидок

- **20% скидка** применяется ко всем детям пользователя, кроме первого
- **Приоритет скидки:** Скидка применяется к **новым подпискам**, а не к уже оплаченным
- **Логика выбора плана для скидки:**
  - Если все подписки новые → скидка к самому дешевому плану
  - Если есть оплаченные и новые → скидка к новой подписке (или к самой дешевой из новых)
  - Если все подписки оплачены → скидок нет
- **Неизменность оплаченных подписок:** Оплаченные подписки не изменяются при добавлении новых детей

### Статусы подписок для расчета скидок

#### ✅ **Учитываемые статусы:**

- `PENDING_PAYMENT` - ожидает оплаты (новая подписка)
- `ACTIVE` - активная и оплаченная подписка
- `PAUSED` - приостановленная, но оплаченная подписка

#### ❌ **Исключаемые статусы:**

- `CANCELLED` - отмененная подписка (не влияет на скидки)
- `EXPIRED` - истекшая подписка (не влияет на скидки)

#### 📋 **Логика определения статуса:**

```python
# Подписка считается "активной" если:
- payment.status == "completed"
- expires_at > текущее_время
- is_paused == False

# Подписка считается "новой" если:
- payment.status != "completed" или payment == None
- status == "pending_payment"

# Подписка исключается из расчета если:
- status == "cancelled" или "expired"
- payment.status == "failed", "refunded", "expired"
```

### Примеры применения скидок

**Сценарий 1: Новые подписки**

- Ребенок 1: план "Базовый" (6 игрушек) - $100/мес
- Ребенок 2: план "Премиум" (9 игрушек) - $150/мес
- **Результат:** Скидка 20% применяется к "Базовому" плану = $80 вместо $100

**Сценарий 2: Новые подписки**

- Ребенок 1: план "Премиум" (9 игрушек) - $150/мес
- Ребенок 2: план "Базовый" (6 игрушек) - $100/мес
- **Результат:** Скидка 20% применяется к "Базовому" плану = $80 вместо $100

**Сценарий 3: Уже есть оплаченная подписка**

- Ребенок 1: план "Базовый" (6 игрушек) - $100/мес (уже оплачен)
- Ребенок 2: план "Премиум" (9 игрушек) - $150/мес (новая подписка)
- **Результат:** Скидка 20% применяется к НОВОЙ подписке "Премиум" = $120 вместо $150
- **Примечание:** Оплаченная подписка остается без изменений

**Сценарий 4: Множественные подписки**

- Ребенок 1: план "Базовый" (6 игрушек) - $100/мес (уже оплачен)
- Ребенок 2: план "Стандарт" (8 игрушек) - $120/мес (уже оплачен)
- Ребенок 3: план "Премиум" (9 игрушек) - $150/мес (новая подписка)
- **Результат:** Скидка 20% применяется к НОВОЙ подписке "Премиум" = $120 вместо $150
- **Примечание:** Существующие оплаченные подписки остаются без изменений

**Сценарий 5: С отмененными подписками**

- Ребенок 1: план "Базовый" (6 игрушек) - $100/мес (статус: CANCELLED)
- Ребенок 2: план "Премиум" (9 игрушек) - $150/мес (новая подписка)
- **Результат:** Скидка 20% применяется к "Премиум" = $120 вместо $150
- **Примечание:** Отмененная подписка не учитывается в расчете

**Сценарий 6: С приостановленными подписками**

- Ребенок 1: план "Базовый" (6 игрушек) - $100/мес (статус: PAUSED, оплачен)
- Ребенок 2: план "Премиум" (9 игрушек) - $150/мес (новая подписка)
- **Результат:** Скидка 20% применяется к "Премиум" = $120 вместо $150
- **Примечание:** Приостановленная оплаченная подписка учитывается как "оплаченная"

## Текущее состояние

### ✅ Что уже работает

- Поле `discount_percent` в модели `Subscription` уже существует
- Логика расчета скидки 20% для второго ребенка и далее уже реализована
- Поле `individual_price` в `Subscription` для хранения финальной цены

### ❌ Что нужно исправить

- `individual_price` сохраняется без учета скидки (равен `plan.price_monthly`)
- Фронтенд показывает `plan.price_monthly` вместо цены со скидкой
- Отсутствует логика применения скидки к самому дешевому плану
- **ВАЖНО:** Необходимо учесть, что оплаченные подписки не должны изменяться при добавлении новых детей

## План реализации

### 1. Обновить логику расчета скидок

**Файл:** `server/services/subscription_service.py`

```python
def _calculate_discount_for_user(self, user_id: int) -> Dict[int, float]:
    """Рассчитывает скидки для всех детей пользователя"""
    children = self.child_repo.get_by_parent_id(user_id)

    if len(children) <= 1:
        return {child.id: 0.0 for child in children}

    # Получаем все релевантные подписки (исключаем отмененные и истекшие)
    subscriptions = []
    for child in children:
        # Получаем активную подписку
        subscription = self.subscription_repo.get_active_by_child_id(child.id)
        if subscription and subscription.status not in [SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]:
            subscriptions.append(subscription)
            continue

        # Получаем ожидающую оплаты подписку
        subscription = self.subscription_repo.get_pending_payment_by_child_id(child.id)
        if subscription and subscription.status not in [SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]:
            subscriptions.append(subscription)
            continue

        # Получаем приостановленную подписку (если есть)
        paused_subscription = self.subscription_repo.get_paused_by_child_id(child.id)
        if paused_subscription and paused_subscription.status == SubscriptionStatus.PAUSED:
            subscriptions.append(paused_subscription)

    if len(subscriptions) <= 1:
        return {child.id: 0.0 for child in children}

    # Разделяем подписки на оплаченные и новые
    paid_subscriptions = [
        s for s in subscriptions
        if s.payment and s.payment.status == PaymentStatus.COMPLETED
        and s.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED]
    ]
    new_subscriptions = [
        s for s in subscriptions
        if not s.payment or s.payment.status != PaymentStatus.COMPLETED
        or s.status == SubscriptionStatus.PENDING_PAYMENT
    ]

    # Если есть только оплаченные подписки - скидок нет
    if not new_subscriptions:
        return {child.id: 0.0 for child in children}

    # Если есть только новые подписки - применяем старую логику
    if not paid_subscriptions:
        cheapest_subscription = min(subscriptions, key=lambda s: s.plan.price_monthly)
        discounts = {}
        for child in children:
            child_subscription = next((s for s in subscriptions if s.child_id == child.id), None)
            if child_subscription and child_subscription.id == cheapest_subscription.id:
                discounts[child.id] = 20.0
            else:
                discounts[child.id] = 0.0
        return discounts

    # Если есть и оплаченные, и новые подписки - скидка только к новой
    if len(new_subscriptions) == 1:
        # Одна новая подписка - применяем к ней скидку
        new_subscription = new_subscriptions[0]
        discounts = {}
        for child in children:
            child_subscription = next((s for s in subscriptions if s.child_id == child.id), None)
            if child_subscription and child_subscription.id == new_subscription.id:
                discounts[child.id] = 20.0
            else:
                discounts[child.id] = 0.0
        return discounts
    else:
        # Несколько новых подписок - применяем к самой дешевой из новых
        cheapest_new_subscription = min(new_subscriptions, key=lambda s: s.plan.price_monthly)
        discounts = {}
        for child in children:
            child_subscription = next((s for s in subscriptions if s.child_id == child.id), None)
            if child_subscription and child_subscription.id == cheapest_new_subscription.id:
                discounts[child.id] = 20.0
            else:
                discounts[child.id] = 0.0
        return discounts
```

### 2. Исправить создание подписки

**Файл:** `server/services/subscription_service.py`

```python
def create_subscription_order(self, request: SubscriptionCreateRequest) -> SubscriptionResponse:
    # ... существующий код ...

    # Рассчитываем скидки для всех детей пользователя
    discounts = self._calculate_discount_for_user(child.parent_id)
    discount_percent = discounts.get(child.id, 0.0)

    # Рассчитываем финальную цену
    final_price = plan.price_monthly * (1 - discount_percent / 100)

    subscription = Subscription(
        child_id=request.child_id,
        plan_id=request.plan_id,
        delivery_info_id=request.delivery_info_id,
        discount_percent=discount_percent,
        individual_price=final_price,  # Сохраняем цену со скидкой
        expires_at=datetime.now(timezone.utc) + relativedelta(months=1)
    )
```

### 3. Добавить поле final_price в схемы ответов

**Файл:** `server/schemas/subscription_schemas.py`

```python
class SubscriptionWithDetailsResponse(BaseModel):
    # ... существующие поля ...
    plan_price: float  # Базовая цена плана
    final_price: float  # Цена со скидкой

    class Config:
        from_attributes = True
```

### 4. Обновить сервис для возврата final_price

**Файл:** `server/services/subscription_service.py`

```python
def get_user_subscriptions(self, user_id: int) -> List[SubscriptionWithDetailsResponse]:
    # ... существующий код ...

    subscription_data = SubscriptionWithDetailsResponse(
        # ... существующие поля ...
        plan_price=subscription.plan.price_monthly,
        final_price=subscription.individual_price,  # Цена со скидкой
        # ... остальные поля ...
    )
```

### 5. Добавить метод пересчета скидок

**Файл:** `server/services/subscription_service.py`

```python
def recalculate_discounts_for_user(self, user_id: int) -> None:
    """Пересчитывает скидки для всех подписок пользователя"""
    discounts = self._calculate_discount_for_user(user_id)

    for child_id, discount_percent in discounts.items():
        subscription = self.subscription_repo.get_active_by_child_id(child_id)
        if not subscription:
            subscription = self.subscription_repo.get_pending_payment_by_child_id(child_id)

        if subscription:
            # Пересчитываем цену
            new_price = subscription.plan.price_monthly * (1 - discount_percent / 100)

            # Обновляем подписку
            update_data = SubscriptionUpdateFields(
                discount_percent=discount_percent,
                individual_price=new_price
            )
            self.subscription_repo.update(subscription.id, update_data)
```

### 6. Добавить пересчеты скидок во всех критических точках

#### 6.1. При создании новой подписки

**Файл:** `server/services/subscription_service.py`

```python
def create_subscription_order(self, request: SubscriptionCreateRequest) -> SubscriptionResponse:
    # ... существующий код создания подписки ...

    # ПОСЛЕ создания подписки пересчитываем скидки для всех детей пользователя
    self.recalculate_discounts_for_user(child.parent_id)

    return subscription_response
```

#### 6.2. При изменении плана подписки

**Файл:** `server/services/subscription_service.py`

```python
def update_subscription(self, subscription_id: int, update_data: SubscriptionUpdateRequest) -> Optional[Subscription]:
    # ... существующий код обновления ...

    # ПОСЛЕ обновления пересчитываем скидки для всех детей пользователя
    subscription = self.subscription_repo.get_by_id(subscription_id)
    if subscription:
        self.recalculate_discounts_for_user(subscription.child.parent_id)

    return updated_subscription
```

#### 6.3. При добавлении нового ребенка

**Файл:** `server/services/child_service.py`

```python
def create_child(self, request: ChildCreateRequest) -> ChildResponse:
    # ... существующий код создания ребенка ...

    # ПОСЛЕ создания ребенка пересчитываем скидки для всех детей пользователя
    subscription_service = SubscriptionService(self.db)
    subscription_service.recalculate_discounts_for_user(request.parent_id)

    return child_response
```

#### 6.4. При удалении ребенка

**Файл:** `server/services/child_service.py`

```python
def delete_child(self, child_id: int, user_id: int) -> bool:
    # ... существующий код удаления ребенка ...

    # ПОСЛЕ удаления ребенка пересчитываем скидки для оставшихся детей
    subscription_service = SubscriptionService(self.db)
    subscription_service.recalculate_discounts_for_user(user_id)

    return True
```

#### 6.5. При отмене подписки

**Файл:** `server/services/subscription_service.py`

```python
def cancel_child_subscription_with_refund(self, child_id: int) -> bool:
    # ... существующий код отмены подписки ...

    # ПОСЛЕ отмены пересчитываем скидки для всех детей пользователя
    subscription = self.subscription_repo.get_by_id(child_id)
    if subscription:
        self.recalculate_discounts_for_user(subscription.child.parent_id)

    return True
```

#### 6.6. API эндпоинт для ручного пересчета

**Файл:** `server/api/subscriptions.py`

```python
@router.post("/recalculate-discounts", response_model=Dict[str, str])
async def recalculate_user_discounts(
    current_user: UserFromToken = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Пересчитывает скидки для всех подписок пользователя"""
    try:
        subscription_service.recalculate_discounts_for_user(current_user.id)
        return {"message": "Скидки пересчитаны"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 7. Обновить фронтенд

**Файл:** `web/src/components/auth/steps/PaymentStep.tsx`

```typescript
// Подсчет общей цены с учетом скидок
const totalPrice = useMemo(
  () =>
    children.reduce((sum, child) => {
      const pendingSubscription = child.subscriptions.filter(
        (subscription) =>
          subscription.status === SubscriptionStatus.pending_payment
      );
      if (pendingSubscription.length > 0) {
        let price = 0;

        for (const subscription of pendingSubscription) {
          // Используем individual_price вместо plan.price_monthly
          price += subscription.individual_price || 0;
        }

        // Округляем цену
        price = Math.round(price);

        return sum + price;
      }

      return sum;
    }, 0),
  [children]
);
```

**Файл:** `web/src/widgets/child-info/ChildInfoWidget.tsx`

```typescript
{
  /* Subscription */
}
{
  subscriptionPlan && (
    <div className="mb-4">
      <p className="text-sm text-gray-600 mb-2">Тариф</p>
      <Tag>
        {subscriptionPlan?.name} • {subscriptionPlan?.toy_count} игрушек • $
        {subscription?.individual_price || subscriptionPlan?.price_monthly} /мес
      </Tag>
    </div>
  );
}
```

### 8. Миграция данных

**Создать миграцию для пересчета цен существующих подписок:**

```python
# migration_script.py
def migrate_existing_subscriptions():
    """Пересчитывает цены для существующих подписок"""
    subscriptions = db.query(Subscription).all()

    for subscription in subscriptions:
        # Рассчитываем скидку
        discount_percent = subscription.discount_percent or 0.0

        # Пересчитываем цену
        new_price = subscription.plan.price_monthly * (1 - discount_percent / 100)

        # Обновляем подписку
        subscription.individual_price = new_price

    db.commit()
```

## Моменты пересчета скидок

### Критические точки для пересчета

Скидки должны пересчитываться в следующих случаях:

#### 1. **Изменение количества детей**

- ✅ Добавление нового ребенка
- ✅ Удаление ребенка
- ✅ Изменение статуса ребенка (активен/неактивен)

#### 2. **Изменение подписок**

- ✅ Создание новой подписки
- ✅ Изменение плана подписки
- ✅ Отмена подписки
- ✅ Возобновление подписки после паузы

#### 3. **Изменение планов**

- ✅ Изменение цены плана (если такое возможно)
- ✅ Изменение состава плана

#### 4. **Системные события**

- ✅ Принудительный пересчет через API
- ✅ Миграция данных
- ✅ Восстановление после сбоев

### Логика пересчета

```python
def recalculate_discounts_for_user(self, user_id: int) -> None:
    """Пересчитывает скидки для всех подписок пользователя"""
    # 1. Получаем всех детей пользователя
    children = self.child_repo.get_by_parent_id(user_id)

    # 2. Получаем все релевантные подписки (исключаем отмененные и истекшие)
    subscriptions = []
    for child in children:
        # Получаем активную подписку
        subscription = self.subscription_repo.get_active_by_child_id(child.id)
        if subscription and subscription.status not in [SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]:
            subscriptions.append(subscription)
            continue

        # Получаем ожидающую оплаты подписку
        subscription = self.subscription_repo.get_pending_payment_by_child_id(child.id)
        if subscription and subscription.status not in [SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]:
            subscriptions.append(subscription)
            continue

        # Получаем приостановленную подписку (если есть)
        paused_subscription = self.subscription_repo.get_paused_by_child_id(child.id)
        if paused_subscription and paused_subscription.status == SubscriptionStatus.PAUSED:
            subscriptions.append(paused_subscription)

    # 3. Если подписок меньше 2 - скидок нет
    if len(subscriptions) <= 1:
        for subscription in subscriptions:
            self._update_subscription_price(subscription.id, 0.0)
        return

    # 4. Разделяем подписки на оплаченные и новые
    paid_subscriptions = [
        s for s in subscriptions
        if s.payment and s.payment.status == PaymentStatus.COMPLETED
        and s.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED]
    ]
    new_subscriptions = [
        s for s in subscriptions
        if not s.payment or s.payment.status != PaymentStatus.COMPLETED
        or s.status == SubscriptionStatus.PENDING_PAYMENT
    ]

    # 5. Если есть только оплаченные подписки - скидок нет
    if not new_subscriptions:
        for subscription in subscriptions:
            self._update_subscription_price(subscription.id, 0.0)
        return

    # 6. Если есть только новые подписки - применяем старую логику
    if not paid_subscriptions:
        cheapest_subscription = min(subscriptions, key=lambda s: s.plan.price_monthly)
        for subscription in subscriptions:
            if subscription.id == cheapest_subscription.id:
                self._update_subscription_price(subscription.id, 20.0)
            else:
                self._update_subscription_price(subscription.id, 0.0)
        return

    # 7. Если есть и оплаченные, и новые подписки
    # Оплаченные подписки оставляем без изменений
    for subscription in paid_subscriptions:
        self._update_subscription_price(subscription.id, 0.0)

    # К новым подпискам применяем скидку
    if len(new_subscriptions) == 1:
        # Одна новая подписка - применяем к ней скидку
        self._update_subscription_price(new_subscriptions[0].id, 20.0)
    else:
        # Несколько новых подписок - применяем к самой дешевой из новых
        cheapest_new_subscription = min(new_subscriptions, key=lambda s: s.plan.price_monthly)
        for subscription in new_subscriptions:
            if subscription.id == cheapest_new_subscription.id:
                self._update_subscription_price(subscription.id, 20.0)
            else:
                self._update_subscription_price(subscription.id, 0.0)

def _update_subscription_price(self, subscription_id: int, discount_percent: float) -> None:
    """Обновляет цену подписки с учетом скидки"""
    subscription = self.subscription_repo.get_by_id(subscription_id)
    if subscription:
        new_price = subscription.plan.price_monthly * (1 - discount_percent / 100)
        update_data = SubscriptionUpdateFields(
            discount_percent=discount_percent,
            individual_price=new_price
        )
        self.subscription_repo.update(subscription_id, update_data)
```

### Оптимизация производительности

#### Проблемы

- Пересчет при каждом изменении может быть медленным
- Множественные обновления БД
- Возможные race conditions

#### Решения

1. **Кэширование результатов** - кэшировать скидки на 5-10 минут
2. **Batch обновления** - обновлять все подписки одним запросом
3. **Асинхронность** - выполнять пересчет в фоне для некритичных операций
4. **Debouncing** - группировать частые изменения

```python
# Пример оптимизированного пересчета
def recalculate_discounts_for_user_optimized(self, user_id: int) -> None:
    """Оптимизированный пересчет скидок"""
    cache_key = f"discounts_user_{user_id}"

    # Проверяем кэш
    cached_discounts = self.cache.get(cache_key)
    if cached_discounts:
        return cached_discounts

    # Выполняем пересчет
    discounts = self._calculate_discount_for_user(user_id)

    # Batch обновление всех подписок
    self._batch_update_subscription_prices(discounts)

    # Кэшируем результат
    self.cache.set(cache_key, discounts, timeout=300)  # 5 минут
```

## Тестирование

### Тестовые сценарии

#### Базовые сценарии

1. **Один ребенок** - скидка не применяется
2. **Два ребенка с одинаковыми планами** - скидка 20% к одному из планов
3. **Два ребенка с разными планами** - скидка 20% к самому дешевому плану
4. **Три ребенка с разными планами** - скидка 20% к самому дешевому плану
5. **Изменение плана** - пересчет скидок при изменении плана

#### Сценарии с оплаченными подписками

6. **Оплаченная + новая подписка** - скидка только к новой
7. **Две оплаченные + новая** - скидка только к новой
8. **Оплаченная + две новые** - скидка к самой дешевой из новых

#### Сценарии со статусами

9. **Отмененная подписка** - не учитывается в расчете
10. **Истекшая подписка** - не учитывается в расчете
11. **Приостановленная оплаченная** - учитывается как оплаченная
12. **Приостановленная неоплаченная** - учитывается как новая
13. **Неудачный платеж** - учитывается как новая подписка
14. **Возврат платежа** - не учитывается в расчете

#### Сценарии с множественными статусами

15. **Отмененная + активная + новая** - скидка к новой
16. **Истекшая + приостановленная + новая** - скидка к новой
17. **Все отменены + новая** - скидка к новой
18. **Все истекли + новая** - скидка к новой

### Проверка результатов

- [ ] Цены в интерфейсе показывают стоимость со скидкой
- [ ] Общая сумма платежа корректно рассчитывается
- [ ] Скидка применяется к самому дешевому плану
- [ ] При добавлении/удалении детей скидки пересчитываются
- [ ] API возвращает корректные данные о ценах

## Риски и ограничения

### Потенциальные проблемы

1. **Производительность** - пересчет скидок при каждом изменении может быть медленным
2. **Консистентность данных** - нужно обеспечить синхронизацию скидок между подписками
3. **Сложность логики** - бизнес-правила могут усложниться в будущем

### Рекомендации

1. **Кэширование** - кэшировать результаты расчета скидок
2. **Асинхронность** - выполнять пересчет скидок в фоне
3. **Мониторинг** - отслеживать корректность применения скидок
4. **Документация** - поддерживать актуальную документацию бизнес-правил

## Заключение

После реализации этого плана система будет корректно применять скидки согласно бизнес-логике:

- 20% скидка для всех детей кроме первого
- Скидка применяется к самому дешевому плану
- Пользователи видят реальную стоимость с учетом скидок
- Платежи рассчитываются корректно

Никаких изменений в `ToyBox`, `Payment` или других сущностях не требуется, так как они не содержат информации о ценах.
