from sqlalchemy.orm import Session
from models.user import User
from models.child import Child
from typing import Optional, List


class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получает пользователя по ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def update_user_profile(self, user_id: int, name: str) -> Optional[User]:
        """Обновляет профиль пользователя"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.name = name
        self.db.flush()  # Только flush для применения изменений
        self.db.refresh(user)
        return user
    
    def get_user_with_children(self, user_id: int) -> Optional[User]:
        """Получает пользователя с детьми"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_all_users(self) -> List[User]:
        """Получает всех пользователей (для админки)"""
        return self.db.query(User).all() 