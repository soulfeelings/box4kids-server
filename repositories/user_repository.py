from typing import Optional, List
from sqlalchemy.orm import Session
from core.interfaces import IUserRepository
from models.user import User


class UserRepository(IUserRepository):
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, db: Session):
        self._db = db
    
    def create(self, phone_number: str, name: Optional[str] = None) -> User:
        user = User(phone_number=phone_number, name=name)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._db.query(User).filter(User.id == user_id).first()
    
    def get_by_phone(self, phone_number: str) -> Optional[User]:
        return self._db.query(User).filter(User.phone_number == phone_number).first()
    
    def get_all(self) -> List[User]:
        return self._db.query(User).all()
    
    def update(self, user: User) -> User:
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if user:
            self._db.delete(user)
            self._db.commit()
            return True
        return False 