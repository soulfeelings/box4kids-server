from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from core.database import Base


class PaymeCardToken(Base):
    __tablename__ = "payme_card_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    card_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    card_number: Mapped[str] = mapped_column(String(19), nullable=False)  # маскированный номер
    expire_date: Mapped[str] = mapped_column(String(4), nullable=False)  # MMYY формат
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # SOFT DELETE
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Relationships
    user = relationship("User", back_populates="payme_cards")
    payments = relationship("Payment", foreign_keys="[Payment.payme_card_token_id]")
