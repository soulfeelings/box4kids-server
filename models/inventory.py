from sqlalchemy import ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from datetime import datetime


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("toy_categories.id"), nullable=False, index=True)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)  # Доступно на складе
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)   # Зарезервировано в наборах
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Связь с категорией
    category = relationship("ToyCategory", back_populates="inventory")