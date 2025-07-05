from sqlalchemy.orm import Session
from models.toy_category import ToyCategory
from typing import List, Optional


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