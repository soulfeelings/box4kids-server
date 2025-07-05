from typing import List, Optional
from sqlalchemy.orm import Session
from models.interest import Interest


class InterestRepository:
    """Репозиторий для работы с интересами"""
    
    def __init__(self, db: Session):
        self._db = db
    
    def get_all(self) -> List[Interest]:
        """Получить все интересы"""
        return self._db.query(Interest).all()
    
    def get_by_ids(self, ids: List[int]) -> List[Interest]:
        """Получить интересы по списку ID"""
        return self._db.query(Interest).filter(Interest.id.in_(ids)).all()
    
    def get_by_id(self, interest_id: int) -> Optional[Interest]:
        """Получить интерес по ID"""
        return self._db.query(Interest).filter(Interest.id == interest_id).first()
    
    def create(self, name: str) -> Interest:
        """Создать новый интерес"""
        interest = Interest(name=name)
        self._db.add(interest)
        self._db.flush()  # Только flush для получения ID
        self._db.refresh(interest)
        return interest
    
    def create_many(self, interests_data: List[dict]) -> List[Interest]:
        """Создать несколько интересов"""
        interests = []
        for data in interests_data:
            interest = Interest(**data)
            interests.append(interest)
        
        self._db.add_all(interests)
        self._db.flush()  # Только flush для получения ID
        
        # Refresh all objects
        for interest in interests:
            self._db.refresh(interest)
        
        return interests 