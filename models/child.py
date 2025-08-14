from sqlalchemy import Integer, String, ForeignKey, Enum, Date, Boolean, Text, DateTime, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
from datetime import datetime
from core.database import Base


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class Child(Base):
    __tablename__ = "children"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[Date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False)
    has_limitations: Mapped[bool] = mapped_column(Boolean, default=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    parent = relationship("User", back_populates="children")
    interests = relationship("Interest", secondary="child_interests", back_populates="children")
    skills = relationship("Skill", secondary="child_skills", back_populates="children")
    subscriptions = relationship("Subscription", back_populates="child")
    
    # Indexes
    __table_args__ = (
        Index('idx_children_parent_not_deleted', 'parent_id', 'is_deleted'),
    ) 