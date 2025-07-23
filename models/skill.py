from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


# Связующая таблица для many-to-many связи между Child и Skill
child_skills = Table(
    'child_skills',
    Base.metadata,
    Column('child_id', Integer, ForeignKey('children.id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
)


class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Relationships
    children = relationship("Child", secondary=child_skills, back_populates="skills")
    categories = relationship("ToyCategory", secondary="category_skills", back_populates="skills") 