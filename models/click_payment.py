from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from core.database import Base


class ClickPaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ClickCardToken(Base):
    __tablename__ = "click_card_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    card_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    card_number: Mapped[str] = mapped_column(String(19), nullable=False)
    expire_date: Mapped[str] = mapped_column(String(4), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Relationships
    user = relationship("User", back_populates="click_cards")
    payments = relationship("ClickPayment", back_populates="card_token")


class ClickPayment(Base):
    __tablename__ = "click_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    card_token_id: Mapped[int] = mapped_column(Integer, ForeignKey("click_card_tokens.id"), nullable=True)
    subscription_ids: Mapped[str] = mapped_column(Text, nullable=False)  # JSON массив ID подписок
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # в тийинах
    merchant_trans_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    merchant_prepare_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    click_payment_id: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[ClickPaymentStatus] = mapped_column(String(20), default=ClickPaymentStatus.PENDING)
    click_trans_id: Mapped[str] = mapped_column(String(255), nullable=True)
    error_code: Mapped[int] = mapped_column(Integer, nullable=True)
    error_note: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Relationships
    user = relationship("User")
    card_token = relationship("ClickCardToken", back_populates="payments")
