from sqlalchemy.orm import Session
from models.interest import Interest
from models.skill import Skill
from repositories.interest_repository import InterestRepository
from repositories.skill_repository import SkillRepository


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


def initialize_all_data(db: Session) -> None:
    """Инициализация всех данных"""
    print("Инициализация данных...")
    
    try:
        initialize_interests(db)
        initialize_skills(db)
        print("Инициализация данных завершена")
    except Exception as e:
        print(f"Ошибка при инициализации данных: {e}")
        raise 