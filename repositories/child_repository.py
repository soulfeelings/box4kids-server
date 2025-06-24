from typing import Optional, List
from sqlalchemy.orm import Session
from models.child import Child
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
        return self._db.query(Child).filter(Child.id == child_id).first()
    
    def get_by_parent_id(self, parent_id: int) -> List[Child]:
        return self._db.query(Child).filter(Child.parent_id == parent_id).all()
    
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