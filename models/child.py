from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date, Boolean, Text
from sqlalchemy.orm import relationship
import enum
from core.database import Base


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class Child(Base):
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    has_limitations = Column(Boolean, default=False)
    comment = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    parent = relationship("User", back_populates="children")
    interests = relationship("Interest", secondary="child_interests", back_populates="children")
    skills = relationship("Skill", secondary="child_skills", back_populates="children") 