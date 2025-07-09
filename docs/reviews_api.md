# 📝 API отзывов на наборы игрушек

## Обзор

API для управления отзывами пользователей на наборы игрушек. Поддерживает создание отзывов с рейтингом 1-5 звезд и комментариями.

## Эндпоинты

### POST /api/toy-boxes/{box_id}/review

Добавить отзыв к набору

**Параметры:**

- `box_id` (path) - ID набора игрушек

**Тело запроса:**

```json
{
  "user_id": 1,
  "rating": 5,
  "comment": "Отличный набор! Ребенок в восторге."
}
```

**Поля:**

- `user_id` (обязательно) - ID пользователя
- `rating` (обязательно) - Рейтинг от 1 до 5
- `comment` (опционально) - Комментарий до 500 символов

**Успешный ответ (200):**

```json
{
  "message": "Отзыв добавлен",
  "review": {
    "id": 1,
    "user_id": 1,
    "rating": 5,
    "comment": "Отличный набор! Ребенок в восторге.",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Ошибки:**

- `400` - Набор не найден
- `400` - Нет прав доступа к этому набору
- `400` - Отзыв можно оставить только на доставленный набор
- `400` - Вы уже оставили отзыв на этот набор
- `422` - Ошибка валидации (рейтинг не в диапазоне 1-5)

### GET /api/toy-boxes/{box_id}/reviews

Получить все отзывы для набора

**Параметры:**

- `box_id` (path) - ID набора игрушек

**Ответ (200):**

```json
{
  "reviews": [
    {
      "id": 1,
      "user_id": 1,
      "rating": 5,
      "comment": "Отличный набор!",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "user_id": 2,
      "rating": 4,
      "comment": null,
      "created_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

## Бизнес-логика

### Ограничения

1. **Один отзыв на набор** - пользователь может оставить только один отзыв на каждый набор
2. **Только доставленные наборы** - отзыв можно оставить только на наборы со статусом `DELIVERED`
3. **Права доступа** - отзыв может оставить только родитель ребенка, которому принадлежит набор
4. **Рейтинг** - строго от 1 до 5 звезд
5. **Комментарий** - опционально, максимум 500 символов

### Статусы наборов

- `PLANNED` - запланирован
- `ASSEMBLED` - собран
- `SHIPPED` - отправлен
- `DELIVERED` - доставлен ✅ (можно оставить отзыв)
- `RETURNED` - возвращен

## UI интеграция

### Логика звезд

```javascript
const ratingTexts = {
  1: "Ужасно! Что можно улучшить?",
  2: "Плохо. Что вам особенно не понравилось?",
  3: "Так себе. Что не устроило?",
  4: "Хорошо! Спасибо за оценку! Что вам особенно понравилось?",
  5: "Отлично! Спасибо за оценку! Что вам особенно понравилось?",
};
```

### Пример React компонента

```jsx
const ReviewModal = ({ boxId, userId, onClose }) => {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  const handleSubmit = async () => {
    const response = await fetch(`/api/toy-boxes/${boxId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, rating, comment }),
    });

    if (response.ok) {
      onClose();
      // Показать успех
    } else {
      const error = await response.json();
      // Показать ошибку
    }
  };

  return (
    <div className="review-modal">
      <h3>Как вам набор игрушек?</h3>
      <StarRating rating={rating} onChange={setRating} />
      <p>{ratingTexts[rating]}</p>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Здесь можно оставить комментарий"
        maxLength={500}
      />
      <button onClick={handleSubmit}>Отправить</button>
    </div>
  );
};
```

## Тестирование

Для тестирования API используйте файл `test_reviews.py`:

```bash
python test_reviews.py
```

Тесты покрывают:

- ✅ Создание валидного отзыва
- ✅ Валидацию рейтинга (1-5)
- ✅ Проверку дублирования отзывов
- ✅ Получение списка отзывов
- ✅ Обработку ошибок

## Миграции БД

Модели уже созданы и будут применены при запуске:

- `toy_box_reviews` - таблица отзывов
- Связь с `toy_boxes` и `users` через foreign keys

## Событийная архитектура

После создания отзыва можно добавить событие:

```python
# В будущем - для аналитики
review_event = ToyBoxReviewedEvent(
    box_id=box_id,
    user_id=user_id,
    rating=rating
)
publisher.publish_event(
    exchange=ExchangeNames.BOX4KIDS_EVENTS,
    routing_key=RoutingKeys.TOYBOX_REVIEWED,
    event_data=review_event.to_dict()
)
```
