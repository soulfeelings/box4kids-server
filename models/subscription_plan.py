from sqlalchemy import Integer, String, Float, DateTime, Text, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    price_monthly: Mapped[float] = mapped_column(Float, nullable=False)
    toy_count: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Relationships
    toy_configurations = relationship("PlanToyConfiguration", back_populates="subscription_plan") 