from sqlalchemy.orm import Session
from models.toy_category import ToyCategory
from models.interest import Interest
from models.skill import Skill
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ToyCategoryRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[ToyCategory]:
        """Получить все категории игрушек"""
        return self.db.query(ToyCategory).all()
    
    def get_by_id(self, category_id: int) -> Optional[ToyCategory]:
        """Получить категорию по ID"""
        return self.db.query(ToyCategory).filter(ToyCategory.id == category_id).first()
    
    def get_by_name(self, name: str) -> Optional[ToyCategory]:
        """Получить категорию по имени"""
        return self.db.query(ToyCategory).filter(ToyCategory.name == name).first()
    
    def create(self, category_data: dict) -> ToyCategory:
        """Создать новую категорию"""
        category = ToyCategory(**category_data)
        self.db.add(category)
        self.db.flush()  # Только flush для получения ID
        self.db.refresh(category)
        return category
    
    def create_many(self, categories_data: List[dict]) -> List[ToyCategory]:
        """Создать множество категорий"""
        categories = []
        for category_data in categories_data:
            category = ToyCategory(**category_data)
            self.db.add(category)
            categories.append(category)
        
        self.db.flush()  # Только flush для получения ID
        
        for category in categories:
            self.db.refresh(category)
        
        return categories
    
    def add_interest(self, category_id: int, interest: Interest) -> bool:
        """Добавить интерес к категории"""
        category = self.get_by_id(category_id)
        if not category:
            logger.warning(f"Категория с ID {category_id} не найдена при добавлении интереса {interest.id}")
            return False
        
        if interest not in category.interests:
            category.interests.append(interest)
            self.db.flush()
            self.db.refresh(category)
            logger.debug(f"Добавлен интерес {interest.name} к категории {category.name}")
            return True
        else:
            logger.debug(f"Интерес {interest.name} уже существует в категории {category.name}")
            return False
    
    def add_skill(self, category_id: int, skill: Skill) -> bool:
        """Добавить навык к категории"""
        category = self.get_by_id(category_id)
        if not category:
            logger.warning(f"Категория с ID {category_id} не найдена при добавлении навыка {skill.id}")
            return False
        
        if skill not in category.skills:
            category.skills.append(skill)
            self.db.flush()
            self.db.refresh(category)
            logger.debug(f"Добавлен навык {skill.name} к категории {category.name}")
            return True
        else:
            logger.debug(f"Навык {skill.name} уже существует в категории {category.name}")
            return False
    
    def remove_interest(self, category_id: int, interest: Interest) -> bool:
        """Удалить интерес из категории"""
        category = self.get_by_id(category_id)
        if not category:
            logger.warning(f"Категория с ID {category_id} не найдена при удалении интереса {interest.id}")
            return False
        
        if interest in category.interests:
            category.interests.remove(interest)
            self.db.flush()
            self.db.refresh(category)
            logger.debug(f"Удален интерес {interest.name} из категории {category.name}")
            return True
        else:
            logger.debug(f"Интерес {interest.name} не найден в категории {category.name}")
            return False
    
    def remove_skill(self, category_id: int, skill: Skill) -> bool:
        """Удалить навык из категории"""
        category = self.get_by_id(category_id)
        if not category:
            logger.warning(f"Категория с ID {category_id} не найдена при удалении навыка {skill.id}")
            return False
        
        if skill in category.skills:
            category.skills.remove(skill)
            self.db.flush()
            self.db.refresh(category)
            logger.debug(f"Удален навык {skill.name} из категории {category.name}")
            return True
        else:
            logger.debug(f"Навык {skill.name} не найден в категории {category.name}")
            return False 