from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from core.database import Base

class ToyBoxStatus(enum.Enum):
    PLANNED = "planned"
    ASSEMBLED = "assembled"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"

class ToyBox(Base):
    __tablename__ = "toy_boxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    child_id: Mapped[int] = mapped_column(Integer, ForeignKey("children.id"), nullable=False)
    delivery_info_id: Mapped[int] = mapped_column(Integer, ForeignKey("delivery_info.id"), nullable=True)
    status: Mapped[ToyBoxStatus] = mapped_column(Enum(ToyBoxStatus), default=ToyBoxStatus.PLANNED)
    delivery_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    return_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Состав набора
    items = relationship("ToyBoxItem", back_populates="box", cascade="all, delete-orphan")
    reviews = relationship("ToyBoxReview", back_populates="box", cascade="all, delete-orphan")

class ToyBoxItem(Base):
    __tablename__ = "toy_box_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    box_id: Mapped[int] = mapped_column(Integer, ForeignKey("toy_boxes.id"), nullable=False)
    toy_category_id: Mapped[int] = mapped_column(Integer, ForeignKey("toy_categories.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    box = relationship("ToyBox", back_populates="items")
    category = relationship("ToyCategory")

class ToyBoxReview(Base):
    __tablename__ = "toy_box_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    box_id: Mapped[int] = mapped_column(Integer, ForeignKey("toy_boxes.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    box = relationship("ToyBox", back_populates="reviews") 