from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from datetime import datetime
from typing import Optional

category_interests = Table(
    'category_interests',
    Base.metadata,
    Column('category_id', Integer, ForeignKey('toy_categories.id'), primary_key=True),
    Column('interest_id', Integer, ForeignKey('interests.id'), primary_key=True)
)

category_skills = Table(
    'category_skills',
    Base.metadata,
    Column('category_id', Integer, ForeignKey('toy_categories.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)

class ToyCategory(Base):
    __tablename__ = "toy_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Связи с интересами и навыками
    interests = relationship("Interest", secondary=category_interests)
    skills = relationship("Skill", secondary=category_skills)
    
    # Связь со складом
    inventory = relationship("Inventory", back_populates="category", uselist=False) 