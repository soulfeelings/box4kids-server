from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


# Связующая таблица для many-to-many связи между Child и Interest
child_interests = Table(
    'child_interests',
    Base.metadata,
    Column('child_id', Integer, ForeignKey('children.id'), primary_key=True),
    Column('interest_id', Integer, ForeignKey('interests.id'), primary_key=True)
)


class Interest(Base):
    __tablename__ = "interests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Relationships
    children = relationship("Child", secondary=child_interests, back_populates="interests") 