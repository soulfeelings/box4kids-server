# MVP: Автоматическое распределение игрушек по интересам

## Цель

Реализовать базовую автоматическую генерацию наборов игрушек на основе интересов ребенка с учетом ограничений склада.

## Текущее состояние

- Статичные конфигурации планов (`PlanToyConfiguration`)
- Фиксированные наборы для каждого плана
- Нет связи между интересами ребенка и категориями игрушек
- Нет учета ограничений склада

## MVP решение

### 1. Управляемый маппинг (models/category_mapping.py)

```python
# Связующие таблицы для many-to-many связей
category_interests = Table(
    'category_interests',
    Base.metadata,
    Column('category_id', Integer, ForeignKey('toy_categories.id'), primary_key=True),
    Column('interest_id', Integer, ForeignKey('interests.id'), primary_key=True)
)

category_skills = Table(
    'category_skills',
    Base.metadata,
    Column('category_id', Integer, ForeignKey('toy_categories.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)

# Обновленная модель ToyCategory
class ToyCategory(Base):
    __tablename__ = "toy_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Связи с интересами и навыками
    interests = relationship("Interest", secondary=category_interests)
    skills = relationship("Skill", secondary=category_skills)
```

### 2. Простая модель склада

```python
class ToyInventory(Base):
    __tablename__ = "toy_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("toy_categories.id"), nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)  # Доступно на складе
    # reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)   # Зарезервировано в наборах (для будущего)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

# Начальные данные склада
INVENTORY_INITIAL_DATA = [
    {"category_name": "Конструктор", "available_quantity": 50},
    {"category_name": "Творческий набор", "available_quantity": 30},
    {"category_name": "Мягкая игрушка", "available_quantity": 40},
    {"category_name": "Головоломка", "available_quantity": 15},
    {"category_name": "Премиум-игрушка", "available_quantity": 10},
]

# Динамические лимиты на основе остатков
def get_max_count(category_id, inventory_service):
    inventory = inventory_service.get_by_category_id(category_id)
    if not inventory:
        return 1  # По умолчанию low

    available = inventory.available_quantity  # Убираем reserved_quantity для MVP
    if available <= 5:
        return 1      # low
    elif available <= 15:
        return X // 3 # medium (2 для X=6)
    else:
        return X // 2 # high (3 для X=6)
```

### 3. Алгоритм распределения (ToyBoxService)

1. **Получить интересы и навыки ребенка** из `Child.interests` и `Child.skills`
2. **Получить историю наборов** ребенка из `ToyBox` для анализа предыдущих комбинаций
3. **Найти подходящие категории** по маппингу (интересы И навыки)
4. **Рассчитать скоринг** каждой категории:
   - Скоринг интересов: количество совпадающих интересов / общее количество интересов категории
   - Скоринг навыков: количество совпадающих навыков / общее количество навыков категории
   - Общий скоринг: (скоринг интересов + скоринг навыков) / 2
   - **Штраф за повторения**: уменьшить скоринг категорий, которые были в последних 2-3 наборах
5. **Применить лимиты склада** по уровням запасов
6. **Распределить игрушки** жадным алгоритмом по убыванию скоринга
7. **Валидировать разнообразие**: убедиться, что в наборе не более X категорий
8. **Сгенерировать состав набора** вместо статичной конфигурации

### 4. Изменения в коде

- **models/category_mapping.py**: создать связующие таблицы для маппинга
- **models/toy_inventory.py**: создать модель склада
- **data_initialization.py**: добавить инициализацию склада и начальных связей категорий
- **services/inventory_service.py**: создать сервис для работы со складом
- **services/category_mapping_service.py**: создать сервис для управления маппингом
- **ToyBoxService**: заменить статичную конфигурацию на динамическую генерацию с учетом склада
- **api/admin.py**: добавить эндпоинты для управления складом и маппингом
- **AdminPage.tsx**: добавить интерфейс для управления складом и связями категорий
- **models/toy_box.py**: добавить поле `interest_tags` для тегирования наборов
- **ToyBoxService**: добавить логику тегирования наборов по интересам ребенка

### 5. Параметры алгоритма

- Y = 6 (общее количество игрушек в базовом плане)
- X = 6 (максимальное разнообразие для расчета лимитов)
- Лимиты: low=1, medium=X/3=2, high=X/2=3

## Ограничения MVP

- Простой алгоритм избежания повторений (анализ только последних 2-3 наборов)
- Базовая модель склада (без учета списания при отправке)

## Результат

- Автоматическое распределение по интересам и навыкам ребенка
- Динамические ограничения на основе реальных остатков склада
- Разнообразие наборов с учетом истории (избежание повторений)
- Базовый скоринг категорий с штрафами за повторения
- Валидация количества категорий в наборе (не более X)
- Тегирование наборов по интересам ребенка (для аналитики)
- Админ-панель для управления складом и маппингом категорий

На 24.07.2025 02:19 по времени мск:
❌ НЕ ВЫПОЛНЕНО (4/12 пунктов):
❌ api/admin.py - эндпоинты для управления складом и маппингом
❌ AdminPage.tsx - интерфейс для управления складом и связями категорий
❌ models/toy_box.py - поле interest_tags для тегирования наборов
❌ ToyBoxService - логика тегирования наборов по интересам ребенка

## Следующие шаги (post-MVP)

1. Автоматическое списание со склада при создании наборов
2. Более сложный алгоритм избежания повторений (анализ большего количества наборов)

## Следующие шаги (post-post-MVP)

3. Персонализация по возрасту
4. Учет отзывов родителей
5. Уведомления о низких остатках на складе
6. Расширенная аналитика на основе тегов (отчеты, рекомендации)
