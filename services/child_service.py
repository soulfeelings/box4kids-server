from sqlalchemy.orm import Session
from models.child import Child, Gender
from typing import Optional, List


class ChildService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_child(self, parent_id: int, name: str, age: int, gender: str) -> Child:
        """Создает ребенка"""
        gender_enum = Gender.MALE if gender == "male" else Gender.FEMALE
        
        child = Child(
            name=name,
            age=age,
            gender=gender_enum,
            parent_id=parent_id
        )
        
        self.db.add(child)
        self.db.commit()
        self.db.refresh(child)
        return child
    
    def get_children_by_parent(self, parent_id: int) -> List[Child]:
        """Получает детей пользователя"""
        return self.db.query(Child).filter(Child.parent_id == parent_id).all()
    
    def get_child_by_id(self, child_id: int) -> Optional[Child]:
        """Получает ребенка по ID"""
        return self.db.query(Child).filter(Child.id == child_id).first()
    
    def update_child(self, child_id: int, parent_id: int, **updates) -> Optional[Child]:
        """Обновляет информацию о ребенке"""
        child = self.db.query(Child).filter(
            Child.id == child_id,
            Child.parent_id == parent_id
        ).first()
        
        if not child:
            return None
        
        for field, value in updates.items():
            if value is not None:
                if field == "gender" and isinstance(value, str):
                    value = Gender.MALE if value == "male" else Gender.FEMALE
                setattr(child, field, value)
        
        self.db.commit()
        self.db.refresh(child)
        return child
    
    def delete_child(self, child_id: int, parent_id: int) -> bool:
        """Удаляет ребенка"""
        child = self.db.query(Child).filter(
            Child.id == child_id,
            Child.parent_id == parent_id
        ).first()
        
        if not child:
            return False
        
        self.db.delete(child)
        self.db.commit()
        return True 