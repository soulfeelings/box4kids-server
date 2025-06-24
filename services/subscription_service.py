from sqlalchemy.orm import Session
from models.subscription import Subscription
from typing import Optional, List, Dict
from datetime import datetime, timedelta


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_available_plans(self) -> List[Dict]:
        """Возвращает доступные планы подписки"""
        return [
            {
                "name": "Basic",
                "price": 1990.0,
                "description": "Базовый набор игрушек",
                "features": ["5 игрушек в месяц", "Доставка раз в месяц"]
            },
            {
                "name": "Premium", 
                "price": 2990.0,
                "description": "Расширенный набор игрушек",
                "features": ["8 игрушек в месяц", "Доставка 2 раза в месяц", "Развивающие материалы"]
            }
        ]
    
    def create_subscription(self, user_id: int, plan_name: str) -> Subscription:
        """Создает подписку"""
        plans = {plan["name"]: plan["price"] for plan in self.get_available_plans()}
        
        if plan_name not in plans:
            raise ValueError(f"Неизвестный план: {plan_name}")
        
        # Деактивируем старые подписки
        self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.is_active == True
        ).update({"is_active": False})
        
        subscription = Subscription(
            user_id=user_id,
            plan_name=plan_name,
            price=plans[plan_name],
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        """Получает подписки пользователя"""
        return self.db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).all()
    
    def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Получает активную подписку пользователя"""
        return self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.is_active == True
        ).first() 