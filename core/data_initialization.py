from sqlalchemy.orm import Session
from models.interest import Interest
from models.skill import Skill
from models.toy_category import ToyCategory
from repositories.interest_repository import InterestRepository
from repositories.skill_repository import SkillRepository
from repositories.toy_category_repository import ToyCategoryRepository


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


def initialize_all_data(db: Session) -> None:
    """Инициализация всех данных"""
    print("Инициализация данных...")
    
    try:
        initialize_interests(db)
        initialize_skills(db)
        initialize_toy_categories(db)
        print("Инициализация данных завершена")
    except Exception as e:
        print(f"Ошибка при инициализации данных: {e}")
        raise 