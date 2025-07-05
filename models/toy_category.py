from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base


class ToyCategory(Base):
    __tablename__ = "toy_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) 