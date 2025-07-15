from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from models.child import Child
from models.interest import Interest
from models.skill import Skill
from core.interfaces import IChildRepository
from datetime import datetime, timezone


class ChildRepository(IChildRepository):
    """Репозиторий для работы с детьми"""
    
    def __init__(self, db: Session):
        self._db = db
    
    def create(self, child: Child) -> Child:
        self._db.add(child)
        self._db.flush()  # Только flush для получения ID
        self._db.refresh(child)
        return child
    
    def get_by_id(self, child_id: int) -> Optional[Child]:
        return self._db.query(Child)\
            .options(joinedload(Child.interests), joinedload(Child.skills), joinedload(Child.subscriptions))\
            .filter(Child.id == child_id, Child.is_deleted == False).first()
    
    def get_by_parent_id(self, parent_id: int) -> List[Child]:
        return self._db.query(Child)\
            .options(joinedload(Child.interests), joinedload(Child.skills), joinedload(Child.subscriptions))\
            .filter(Child.parent_id == parent_id, Child.is_deleted == False).all()
    
    def update(self, child: Child) -> Child:
        self._db.flush()  # Только flush для применения изменений
        self._db.refresh(child)
        return child
    
    def delete(self, child_id: int) -> bool:
        child = self._db.query(Child).filter(Child.id == child_id, Child.is_deleted == False).first()
        if not child:
            return False
        
        child.is_deleted = True
        child.deleted_at = datetime.now(timezone.utc)
        self._db.flush()  # Только flush для применения изменений
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
        self._db.flush()  # Только flush для применения изменений
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
        self._db.flush()  # Только flush для применения изменений
        return True 