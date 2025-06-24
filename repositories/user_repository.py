from typing import Optional, List
from sqlalchemy.orm import Session
from models.user import User
from core.interfaces import IUserRepository


class UserRepository(IUserRepository):
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, db: Session):
        self._db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._db.query(User).filter(User.id == user_id).first()
    
    def get_by_phone(self, phone: str) -> Optional[User]:
        return self._db.query(User).filter(User.phone_number == phone).first()
    
    def create(self, user: User) -> User:
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
    
    def update(self, user: User) -> User:
        self._db.commit()
        self._db.refresh(user)
        return user
    
    def get_all(self) -> List[User]:
        return self._db.query(User).all() 