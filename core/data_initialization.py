from sqlalchemy.orm import Session
from repositories.interest_repository import InterestRepository
from repositories.skill_repository import SkillRepository
from repositories.toy_category_repository import ToyCategoryRepository
from repositories.subscription_plan_repository import SubscriptionPlanRepository
from repositories.plan_toy_configuration_repository import PlanToyConfigurationRepository
from repositories.inventory_repository import InventoryRepository
from services.category_mapping_service import CategoryMappingService


# Хардкод данных интересов
INTERESTS_DATA = [
    {"name": "🧸 Конструкторы"},
    {"name": "🧸 Плюшевые"},
    {"name": "🎲 Ролевые"},
    {"name": "🧠 Развивающие"},
    {"name": "⚙️ Техника"},
    {"name": "🎨 Творчество"},
]


# Хардкод данных навыков
SKILLS_DATA = [
    {"name": "✋ Моторика"},
    {"name": "🧠 Логика"},
    {"name": "🎭 Воображение"},
    {"name": "🎨 Творчество"},
    {"name": "💬 Речь"},
]


# Хардкод данных категорий игрушек
TOY_CATEGORIES_DATA = [
    {"name": "Конструктор", "description": "Развивающие конструкторы для детей", "icon": "🧩"},
    {"name": "Творческий набор", "description": "Наборы для творчества и рисования", "icon": "🎨"},
    {"name": "Мягкая игрушка", "description": "Мягкие плюшевые игрушки", "icon": "🧸"},
    {"name": "Головоломка", "description": "Логические игры и головоломки", "icon": "🧠"},
    {"name": "Премиум-игрушка", "description": "Эксклюзивные развивающие игрушки", "icon": "⭐"},
]


# Маппинг категорий с интересами и навыками
CATEGORY_MAPPINGS = {
    "Конструктор": {
        "interests": ["🧸 Конструкторы", "⚙️ Техника"],
        "skills": ["✋ Моторика", "🧠 Логика"]
    },
    "Творческий набор": {
        "interests": ["🎨 Творчество"],
        "skills": ["🎨 Творчество", "🎭 Воображение"]
    },
    "Мягкая игрушка": {
        "interests": ["🧸 Плюшевые", "🎲 Ролевые"],
        "skills": ["🎭 Воображение", "💬 Речь"]
    },
    "Головоломка": {
        "interests": ["🧠 Развивающие"],
        "skills": ["🧠 Логика", "✋ Моторика"]
    },
    "Премиум-игрушка": {
        "interests": ["🧠 Развивающие", "🎨 Творчество"],
        "skills": ["🧠 Логика", "🎨 Творчество", "🎭 Воображение"]
    }
}


# Хардкод данных планов подписки
SUBSCRIPTION_PLANS_DATA = [
    {
        "name": "Базовый",
        "price_monthly": 35.0,
        "toy_count": 6,
        "description": "Базовый набор развивающих игрушек для детей"
    },
    {
        "name": "Премиум",
        "price_monthly": 60.0,
        "toy_count": 9,
        "description": "Премиум набор с эксклюзивными игрушками"
    }
]


# Хардкод данных конфигураций планов (plan_name -> category_name -> quantity)
PLAN_CONFIGURATIONS = {
    "Базовый": {
        "Конструктор": 2,
        "Творческий набор": 2,
        "Мягкая игрушка": 1,
        "Головоломка": 1,
    },
    "Премиум": {
        "Конструктор": 3,
        "Творческий набор": 2,
        "Мягкая игрушка": 2,
        "Головоломка": 1,
        "Премиум-игрушка": 1,
    }
}

def initialize_mock_inventory(db: Session) -> None:
    """Инициализация склада (МОК)"""
    repository = InventoryRepository(db)

    # Проверяем, есть ли уже склад
    invetory = repository.get_all()
    if invetory:
        print("Склад уже инициализирован (мок)")
        return

    data = []

    for category in TOY_CATEGORIES_DATA:
        name = category["name"]
        data.append({
            "category_name": name,
            "available_quantity": 50
        })

    repository.create_many(data)
    print(f"Создано {len(data)} категорий на складе")


def initialize_category_mappings(db: Session) -> None:
    """Инициализация связей между категориями и интересами/навыками"""
    mapping_service = CategoryMappingService(db)
    category_repo = ToyCategoryRepository(db)
    interest_repo = InterestRepository(db)
    skill_repo = SkillRepository(db)
    
    # Проверяем, есть ли уже связи
    categories = category_repo.get_all()
    if categories and categories[0].interests:
        print("Связи категорий уже инициализированы")
        return
    
    print("Инициализация связей категорий с интересами и навыками...")
    
    for category_name, mappings in CATEGORY_MAPPINGS.items():
        category = category_repo.get_by_name(category_name)
        if not category:
            print(f"Категория {category_name} не найдена, пропускаем")
            continue
        
        # Добавляем интересы
        for interest_name in mappings["interests"]:
            interest = interest_repo.get_by_name(interest_name)
            if interest:
                mapping_service.add_interest_to_category(category.id, interest.id)
                print(f"Добавлен интерес {interest_name} к категории {category_name}")
        
        # Добавляем навыки
        for skill_name in mappings["skills"]:
            skill = skill_repo.get_by_name(skill_name)
            if skill:
                mapping_service.add_skill_to_category(category.id, skill.id)
                print(f"Добавлен навык {skill_name} к категории {category_name}")
    
    print("Инициализация связей завершена")


def initialize_interests(db: Session) -> None:
    """Инициализация интересов"""
    repository = InterestRepository(db)
    
    # Проверяем, есть ли уже интересы
    existing_interests = repository.get_all()
    if existing_interests:
        print("Интересы уже инициализированы")
        return
    
    # Создаем интересы
    interests = repository.create_many(INTERESTS_DATA)
    print(f"Создано {len(interests)} интересов")


def initialize_skills(db: Session) -> None:
    """Инициализация навыков"""
    repository = SkillRepository(db)
    
    # Проверяем, есть ли уже навыки
    existing_skills = repository.get_all()
    if existing_skills:
        print("Навыки уже инициализированы")
        return
    
    # Создаем навыки
    skills = repository.create_many(SKILLS_DATA)
    print(f"Создано {len(skills)} навыков")


def initialize_toy_categories(db: Session) -> None:
    """Инициализация категорий игрушек"""
    repository = ToyCategoryRepository(db)
    
    # Проверяем, есть ли уже категории
    existing_categories = repository.get_all()
    if existing_categories:
        print("Категории игрушек уже инициализированы")
        return
    
    # Создаем категории
    categories = repository.create_many(TOY_CATEGORIES_DATA)
    print(f"Создано {len(categories)} категорий игрушек")


def initialize_subscription_plans(db: Session) -> None:
    """Инициализация планов подписки"""
    plan_repository = SubscriptionPlanRepository(db)
    
    # Проверяем, есть ли уже планы
    existing_plans = plan_repository.get_all()
    if existing_plans:
        print("Планы подписки уже инициализированы")
        return
    
    # Создаем планы
    plans = plan_repository.create_many(SUBSCRIPTION_PLANS_DATA)
    print(f"Создано {len(plans)} планов подписки")


def initialize_plan_toy_configurations(db: Session) -> None:
    """Инициализация конфигураций планов"""
    plan_repository = SubscriptionPlanRepository(db)
    category_repository = ToyCategoryRepository(db)
    config_repository = PlanToyConfigurationRepository(db)
    
    # Проверяем, есть ли уже конфигурации
    existing_configs = config_repository.get_all()
    if existing_configs:
        print("Конфигурации планов уже инициализированы")
        return
    
    # Создаем конфигурации
    configs_data = []
    for plan_name, categories_config in PLAN_CONFIGURATIONS.items():
        # Находим план по имени
        plan = plan_repository.get_by_name(plan_name)
        if not plan:
            print(f"План {plan_name} не найден")
            continue
        
        for category_name, quantity in categories_config.items():
            # Находим категорию по имени
            category = category_repository.get_by_name(category_name)
            if not category:
                print(f"Категория {category_name} не найдена")
                continue
            
            configs_data.append({
                "plan_id": plan.id,
                "category_id": category.id,
                "quantity": quantity
            })
    
    # Создаем конфигурации
    configs = config_repository.create_many(configs_data)
    print(f"Создано {len(configs)} конфигураций планов")


def initialize_all_data(db: Session) -> None:
    """Инициализация всех данных"""
    print("Инициализация данных.......")
    
    try:
        initialize_interests(db)
        initialize_skills(db)
        initialize_toy_categories(db)
        initialize_subscription_plans(db)
        initialize_plan_toy_configurations(db)
        initialize_mock_inventory(db)
        initialize_category_mappings(db) # Добавляем вызов новой функции
        db.commit()
        print("Инициализация данных завершена")
    except Exception as e:
        print(f"Ошибка при инициализации данных: {e}")
        db.rollback()
        raise 