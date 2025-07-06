from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class PlanToyConfiguration(Base):
    __tablename__ = "plan_toy_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("toy_categories.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    # Relationships
    subscription_plan = relationship("SubscriptionPlan", back_populates="toy_configurations")
    category = relationship("ToyCategory") 