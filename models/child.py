from sqlalchemy import Column, Integer, String, ForeignKey, Enum
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
    age = Column(Integer, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    parent = relationship("User", back_populates="children") 