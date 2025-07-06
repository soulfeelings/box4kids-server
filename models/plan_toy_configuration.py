from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core.database import Base


class PlanToyConfiguration(Base):
    __tablename__ = "plan_toy_configurations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("toy_categories.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    subscription_plan = relationship("SubscriptionPlan", back_populates="toy_configurations")
    category = relationship("ToyCategory") 