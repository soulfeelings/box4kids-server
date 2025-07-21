# План внедрения системы скидок

## Бизнес-логика

### Правила скидок

- **20% скидка** применяется ко всем детям пользователя, кроме первого
- Скидка применяется к **самому дешевому плану** среди всех детей пользователя
- Если у пользователя несколько детей с разными планами, скидка применяется к плану с наименьшей стоимостью

### Примеры применения скидок

**Сценарий 1:**

- Ребенок 1: план "Базовый" (6 игрушек) - $100/мес
- Ребенок 2: план "Премиум" (9 игрушек) - $150/мес
- **Результат:** Скидка 20% применяется к "Базовому" плану = $80 вместо $100

**Сценарий 2:**

- Ребенок 1: план "Премиум" (9 игрушек) - $150/мес
- Ребенок 2: план "Базовый" (6 игрушек) - $100/мес
- **Результат:** Скидка 20% применяется к "Базовому" плану = $80 вместо $100

## Текущее состояние

### ✅ Что уже работает

- Поле `discount_percent` в модели `Subscription` уже существует
- Логика расчета скидки 20% для второго ребенка и далее уже реализована
- Поле `individual_price` в `Subscription` для хранения финальной цены

### ❌ Что нужно исправить

- `individual_price` сохраняется без учета скидки (равен `plan.price_monthly`)
- Фронтенд показывает `plan.price_monthly` вместо цены со скидкой
- Отсутствует логика применения скидки к самому дешевому плану

## План реализации

### 1. Обновить логику расчета скидок

**Файл:** `server/services/subscription_service.py`

```python
def _calculate_discount_for_user(self, user_id: int) -> Dict[int, float]:
    """Рассчитывает скидки для всех детей пользователя"""
    children = self.child_repo.get_by_parent_id(user_id)

    if len(children) <= 1:
        return {child.id: 0.0 for child in children}

    # Получаем все активные/ожидающие подписки
    subscriptions = []
    for child in children:
        subscription = self.subscription_repo.get_active_by_child_id(child.id)
        if not subscription:
            subscription = self.subscription_repo.get_pending_payment_by_child_id(child.id)
        if subscription:
            subscriptions.append(subscription)

    if len(subscriptions) <= 1:
        return {child.id: 0.0 for child in children}

    # Находим самую дешевую подписку
    cheapest_subscription = min(subscriptions, key=lambda s: s.plan.price_monthly)

    # Применяем скидку только к самому дешевому плану
    discounts = {}
    for child in children:
        child_subscription = next((s for s in subscriptions if s.child_id == child.id), None)
        if child_subscription and child_subscription.id == cheapest_subscription.id:
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

### 6. Добавить API эндпоинт для пересчета скидок

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

## Тестирование

### Тестовые сценарии

1. **Один ребенок** - скидка не применяется
2. **Два ребенка с одинаковыми планами** - скидка 20% к одному из планов
3. **Два ребенка с разными планами** - скидка 20% к самому дешевому плану
4. **Три ребенка с разными планами** - скидка 20% к самому дешевому плану
5. **Изменение плана** - пересчет скидок при изменении плана

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
