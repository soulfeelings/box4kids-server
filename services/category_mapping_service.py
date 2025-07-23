from typing import List, Dict, Any
from sqlalchemy.orm import Session
from repositories.toy_category_repository import ToyCategoryRepository
from repositories.interest_repository import InterestRepository
from repositories.skill_repository import SkillRepository
from models.toy_category import ToyCategory
import logging

logger = logging.getLogger(__name__)


class CategoryMappingService:
    """Сервис для управления связями категорий с интересами и навыками"""
    
    def __init__(self, db: Session):
        self.db = db
        self.category_repo = ToyCategoryRepository(db)
        self.interest_repo = InterestRepository(db)
        self.skill_repo = SkillRepository(db)
    
    def get_category_score(self, category: ToyCategory, child_interests: List, child_skills: List) -> float:
        """Рассчитать скоринг категории для ребенка"""
        if not child_interests and not child_skills:
            return 0.0
        
        # Скоринг по интересам
        interest_score = 0.0
        if child_interests and category.interests:
            matching_interests = set(child_interests) & set(category.interests)
            interest_score = len(matching_interests) / len(category.interests)
        
        # Скоринг по навыкам
        skill_score = 0.0
        if child_skills and category.skills:
            matching_skills = set(child_skills) & set(category.skills)
            skill_score = len(matching_skills) / len(category.skills)
        
        # Общий скоринг
        if child_interests and child_skills:
            return (interest_score + skill_score) / 2
        elif child_interests:
            return interest_score
        elif child_skills:
            return skill_score
        
        return 0.0
    
    def get_categories_with_scores(self, child_interests: List, child_skills: List) -> List[Dict[str, Any]]:
        """Получить все категории с их скорингом для ребенка"""
        categories = self.category_repo.get_all()
        scored_categories = []
        
        for category in categories:
            score = self.get_category_score(category, child_interests, child_skills)
            scored_categories.append({
                "category": category,
                "score": score
            })
        
        # Сортируем по убыванию скоринга
        scored_categories.sort(key=lambda x: x["score"], reverse=True)
        return scored_categories
    
    def add_interest_to_category(self, category_id: int, interest_id: int) -> bool:
        """Добавить интерес к категории"""
        category = self.category_repo.get_by_id(category_id)
        if not category:
            logger.warning(f"Категория с ID {category_id} не найдена при добавлении интереса {interest_id}")
            return False
        
        interest = self.interest_repo.get_by_id(interest_id)
        if not interest:
            logger.warning(f"Интерес с ID {interest_id} не найден при добавлении к категории {category_id}")
            return False
        
        result = self.category_repo.add_interest(category_id, interest)
        if result:
            logger.info(f"Добавлен интерес {interest.name} к категории {category.name}")
        else:
            logger.info(f"Интерес {interest.name} уже существует в категории {category.name}")
        
        return result
    
    def add_skill_to_category(self, category_id: int, skill_id: int) -> bool:
        """Добавить навык к категории"""
        category = self.category_repo.get_by_id(category_id)
        if not category:
            logger.warning(f"Категория с ID {category_id} не найдена при добавлении навыка {skill_id}")
            return False
        
        skill = self.skill_repo.get_by_id(skill_id)
        if not skill:
            logger.warning(f"Навык с ID {skill_id} не найден при добавлении к категории {category_id}")
            return False
        
        result = self.category_repo.add_skill(category_id, skill)
        if result:
            logger.info(f"Добавлен навык {skill.name} к категории {category.name}")
        else:
            logger.info(f"Навык {skill.name} уже существует в категории {category.name}")
        
        return result
    
    def remove_interest_from_category(self, category_id: int, interest_id: int) -> bool:
        """Удалить интерес из категории"""
        category = self.category_repo.get_by_id(category_id)
        if not category:
            logger.warning(f"Категория с ID {category_id} не найдена при удалении интереса {interest_id}")
            return False
        
        interest = self.interest_repo.get_by_id(interest_id)
        if not interest:
            logger.warning(f"Интерес с ID {interest_id} не найден при удалении из категории {category_id}")
            return False
        
        result = self.category_repo.remove_interest(category_id, interest)
        if result:
            logger.info(f"Удален интерес {interest.name} из категории {category.name}")
        else:
            logger.info(f"Интерес {interest.name} не найден в категории {category.name}")
        
        return result
    
    def remove_skill_from_category(self, category_id: int, skill_id: int) -> bool:
        """Удалить навык из категории"""
        category = self.category_repo.get_by_id(category_id)
        if not category:
            logger.warning(f"Категория с ID {category_id} не найдена при удалении навыка {skill_id}")
            return False
        
        skill = self.skill_repo.get_by_id(skill_id)
        if not skill:
            logger.warning(f"Навык с ID {skill_id} не найден при удалении из категории {category_id}")
            return False
        
        result = self.category_repo.remove_skill(category_id, skill)
        if result:
            logger.info(f"Удален навык {skill.name} из категории {category.name}")
        else:
            logger.info(f"Навык {skill.name} не найден в категории {category.name}")
        
        return result 