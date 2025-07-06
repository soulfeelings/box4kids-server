from sqlalchemy.orm import Session
from models.delivery_info import DeliveryInfo
from typing import List, Optional


class DeliveryInfoRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, delivery_id: int) -> Optional[DeliveryInfo]:
        """Получить адрес доставки по ID"""
        return self.db.query(DeliveryInfo).filter(DeliveryInfo.id == delivery_id).first()
    
    def get_by_user_id(self, user_id: int, limit: Optional[int] = None) -> List[DeliveryInfo]:
        """Получить адреса доставки пользователя!"""
        query = (
            self.db.query(DeliveryInfo)
            .filter(DeliveryInfo.user_id == user_id)
            .order_by(DeliveryInfo.created_at.desc())
        )
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def create(self, delivery_data: dict) -> DeliveryInfo:
        """Создать новый адрес доставки"""
        delivery = DeliveryInfo(**delivery_data)
        self.db.add(delivery)
        self.db.flush()
        self.db.refresh(delivery)
        return delivery
    
    def update(self, delivery_id: int, user_id: int, update_data: dict) -> Optional[DeliveryInfo]:
        """Обновить адрес доставки пользователя"""
        delivery = (
            self.db.query(DeliveryInfo)
            .filter(DeliveryInfo.id == delivery_id, DeliveryInfo.user_id == user_id)
            .first()
        )
        if not delivery:
            return None
        
        for field, value in update_data.items():
            if hasattr(delivery, field):
                setattr(delivery, field, value)
        
        self.db.flush()
        self.db.refresh(delivery)
        return delivery
    
    def delete(self, delivery_id: int, user_id: int) -> bool:
        """Удалить адрес доставки пользователя"""
        delivery = (
            self.db.query(DeliveryInfo)
            .filter(DeliveryInfo.id == delivery_id, DeliveryInfo.user_id == user_id)
            .first()
        )
        if not delivery:
            return False
        
        self.db.delete(delivery)
        self.db.flush()
        return True 