from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from models.child import Child
from models.interest import Interest
from models.skill import Skill
from core.interfaces import IChildRepository


class ChildRepository(IChildRepository):
    """Репозиторий для работы с детьми"""
    
    def __init__(self, db: Session):
        self._db = db
    
    def create(self, child: Child) -> Child:
        self._db.add(child)
        self._db.commit()
        self._db.refresh(child)
        return child
    
    def get_by_id(self, child_id: int) -> Optional[Child]:
        return self._db.query(Child)\
            .options(joinedload(Child.interests), joinedload(Child.skills))\
            .filter(Child.id == child_id).first()
    
    def get_by_parent_id(self, parent_id: int) -> List[Child]:
        return self._db.query(Child)\
            .options(joinedload(Child.interests), joinedload(Child.skills))\
            .filter(Child.parent_id == parent_id).all()
    
    def update(self, child: Child) -> Child:
        self._db.commit()
        self._db.refresh(child)
        return child
    
    def delete(self, child_id: int) -> bool:
        child = self.get_by_id(child_id)
        if not child:
            return False
        
        self._db.delete(child)
        self._db.commit()
        return True
    
    def update_interests(self, child_id: int, interest_ids: List[int]) -> bool:
        """Обновить интересы ребенка"""
        child = self.get_by_id(child_id)
        if not child:
            return False
        
        # Получаем интересы по ID
        interests = self._db.query(Interest).filter(Interest.id.in_(interest_ids)).all()
        
        # Заменяем интересы ребенка
        child.interests = interests
        self._db.commit()
        return True
    
    def update_skills(self, child_id: int, skill_ids: List[int]) -> bool:
        """Обновить навыки ребенка"""
        child = self.get_by_id(child_id)
        if not child:
            return False
        
        # Получаем навыки по ID
        skills = self._db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
        
        # Заменяем навыки ребенка
        child.skills = skills
        self._db.commit()
        return True 