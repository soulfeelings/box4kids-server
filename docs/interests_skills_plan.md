# План реализации: Интересы и навыки детей

## Задача

Добавить функционал интересов и навыков для развития детей:

- Таблица интересов (хардкод)
- Таблица навыков для развития (хардкод)
- API роуты для получения списков
- Связь many-to-many с детьми
- Обновление интересов/навыков через PUT /children/{child_id}

## Модели данных

### Interest (Интересы)

```python
class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    icon = Column(String, nullable=True)  # эмодзи в названии

    # Relationships
    children = relationship("Child", secondary="child_interests", back_populates="interests")
```

### Skill (Навыки для развития)

```python
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    icon = Column(String, nullable=True)  # эмодзи в названии

    # Relationships
    children = relationship("Child", secondary="child_skills", back_populates="skills")
```

### Связующие таблицы

```python
child_interests = Table(
    'child_interests',
    Base.metadata,
    Column('child_id', Integer, ForeignKey('children.id'), primary_key=True),
    Column('interest_id', Integer, ForeignKey('interests.id'), primary_key=True)
)

child_skills = Table(
    'child_skills',
    Base.metadata,
    Column('child_id', Integer, ForeignKey('children.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)
```

### Обновление модели Child

```python
class Child(Base):
    # ... существующие поля ...

    # Relationships
    interests = relationship("Interest", secondary="child_interests", back_populates="children")
    skills = relationship("Skill", secondary="child_skills", back_populates="children")
```

## Схемы (Pydantic)

### Базовые схемы

```python
class InterestBase(BaseModel):
    name: str
    icon: Optional[str] = None

class InterestResponse(InterestBase):
    id: int
    class Config:
        from_attributes = True

class SkillBase(BaseModel):
    name: str
    icon: Optional[str] = None

class SkillResponse(SkillBase):
    id: int
    class Config:
        from_attributes = True
```

### Обновление схем ребенка

```python
class ChildUpdateRequest(BaseModel):
    name: Optional[str] = None
    interest_ids: Optional[List[int]] = None
    skill_ids: Optional[List[int]] = None

class ChildResponse(BaseModel):
    id: int
    name: str
    # ... другие поля ...
    interests: List[InterestResponse] = []
    skills: List[SkillResponse] = []
```

## API эндпоинты

### Новые роуты

```python
# GET /interests - получить все интересы
# GET /skills - получить все навыки
```

### Обновление существующих роутов

```python
# PUT /children/{child_id} - обновить ребенка (включая интересы/навыки)
# GET /children/{child_id} - получить ребенка с интересами/навыками
```

## Репозитории

### InterestRepository

```python
class InterestRepository:
    def get_all(self) -> List[Interest]
    def get_by_ids(self, ids: List[int]) -> List[Interest]
```

### SkillRepository

```python
class SkillRepository:
    def get_all(self) -> List[Skill]
    def get_by_ids(self, ids: List[int]) -> List[Skill]
```

### Обновление ChildRepository

```python
class ChildRepository:
    def update_interests(self, child_id: int, interest_ids: List[int]) -> None
    def update_skills(self, child_id: int, skill_ids: List[int]) -> None
    def get_by_id(self, child_id: int) -> Optional[Child]  # с загрузкой interests/skills
```

## Сервисы

### InterestService

```python
class InterestService:
    def get_all_interests(self) -> List[InterestResponse]
```

### SkillService

```python
class SkillService:
    def get_all_skills(self) -> List[SkillResponse]
```

### Обновление ChildService

```python
class ChildService:
    def update_child(self, child_id: int, data: ChildUpdateRequest) -> ChildResponse
    def get_child_by_id(self, child_id: int) -> Optional[ChildResponse]
```

## Данные (хардкод)

### Интересы

```python
INTERESTS_DATA = [
    {"id": 1, "name": "🧸 Конструкторы"},
    {"id": 2, "name": "🧸 Плюшевые"},
    {"id": 3, "name": "🎲 Ролевые"},
    {"id": 4, "name": "🧠 Развивающие"},
    {"id": 5, "name": "⚙️ Техника"},
    {"id": 6, "name": "🎨 Творчество"},
]
```

### Навыки для развития

```python
SKILLS_DATA = [
    {"id": 1, "name": "✋ Моторика"},
    {"id": 2, "name": "🧠 Логика"},
    {"id": 3, "name": "🎭 Воображение"},
    {"id": 4, "name": "🎨 Творчество"},
    {"id": 5, "name": "💬 Речь"},
]
```

## Этапы реализации

1. **Создание моделей**

   - Interest, Skill модели
   - Связующие таблицы
   - Обновление Child модели

2. **Схемы валидации**

   - InterestResponse, SkillResponse
   - Обновление ChildUpdateRequest, ChildResponse

3. **Репозитории**

   - InterestRepository, SkillRepository
   - Обновление ChildRepository

4. **Сервисы**

   - InterestService, SkillService
   - Обновление ChildService

5. **API эндпоинты**

   - GET /interests, GET /skills
   - Обновление PUT /children/{child_id}

6. **Инициализация данных**
   - Создание хардкод данных при старте приложения

## Тестирование

1. **Unit тесты**

   - Сервисы
   - Репозитории

2. **Integration тесты**
   - API эндпоинты

## Миграции

- Создание таблиц interests, skills, child_interests, child_skills
- Заполнение базовых данных
