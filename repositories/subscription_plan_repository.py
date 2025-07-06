from sqlalchemy.orm import Session
from models.subscription_plan import SubscriptionPlan
from typing import List, Optional


class SubscriptionPlanRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[SubscriptionPlan]:
        """Получить все планы подписки"""
        return self.db.query(SubscriptionPlan).all()
    
    def get_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """Получить план по ID"""
        return self.db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    
    def get_by_name(self, name: str) -> Optional[SubscriptionPlan]:
        """Получить план по имени"""
        return self.db.query(SubscriptionPlan).filter(SubscriptionPlan.name == name).first()
    
    def create(self, plan_data: dict) -> SubscriptionPlan:
        """Создать новый план"""
        plan = SubscriptionPlan(**plan_data)
        self.db.add(plan)
        self.db.flush()
        self.db.refresh(plan)
        return plan
    
    def create_many(self, plans_data: List[dict]) -> List[SubscriptionPlan]:
        """Создать множество планов"""
        plans = []
        for plan_data in plans_data:
            plan = SubscriptionPlan(**plan_data)
            self.db.add(plan)
            plans.append(plan)
        
        self.db.flush()
        
        for plan in plans:
            self.db.refresh(plan)
        
        return plans 