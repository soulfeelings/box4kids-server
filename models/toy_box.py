from sqlalchemy import Integer, ForeignKey, DateTime, Enum, String, Text, Date, func, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date, datetime
import enum
from core.database import Base
from typing import Optional, List

class ToyBoxStatus(enum.Enum):
    """Статусы набора игрушек в процессе аренды"""
    
    PLANNED = "planned"        # 🎯 ToyBox создан после оплаты, ждёт сборки на складе
    ASSEMBLED = "assembled"    # 📋 Игрушки собраны и упакованы, готовы к отправке
    SHIPPED = "shipped"        # 🚚 Набор передан курьеру, в пути к клиенту
    DELIVERED = "delivered"    # ✅ Клиент получил набор, период аренды активен
    RETURNED = "returned"      # 🔄 Игрушки возвращены, набор завершён

class ToyBox(Base):
    __tablename__ = "toy_boxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    child_id: Mapped[int] = mapped_column(Integer, ForeignKey("children.id"), nullable=False)
    delivery_info_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("delivery_info.id"), nullable=True)
    status: Mapped[ToyBoxStatus] = mapped_column(Enum(ToyBoxStatus), default=ToyBoxStatus.PLANNED)
    delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delivery_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    return_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    interest_tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # JSONB массив с интересами или скиллами ребенка
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    box = relationship("ToyBox", back_populates="reviews") 