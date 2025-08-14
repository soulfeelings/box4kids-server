from sqlalchemy import Integer, String, DateTime, Enum, Float, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from core.database import Base


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentType(enum.Enum):
    MOCK = "mock"  # Для тестов и mock gateway
    CLICK = "click"
    PAYME = "payme"


class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="UZS")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Универсальные поля для всех типов платежей
    external_payment_id: Mapped[str] = mapped_column(String, nullable=True)  # ID из внешнего сервиса
    merchant_trans_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Click специфичные поля
    click_trans_id: Mapped[str] = mapped_column(String(255), nullable=True)
    merchant_prepare_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    click_card_token_id: Mapped[int] = mapped_column(Integer, ForeignKey("click_card_tokens.id"), nullable=True)
    
    # Payme специфичные поля  
    payme_receipt_id: Mapped[str] = mapped_column(String(255), nullable=True)
    payme_card_token_id: Mapped[int] = mapped_column(Integer, ForeignKey("payme_card_tokens.id"), nullable=True)
    
    # Дополнительные поля
    error_code: Mapped[int] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="payments")
    subscriptions = relationship("Subscription", back_populates="payment")
    click_card_token = relationship("ClickCardToken")
    payme_card_token = relationship("PaymeCardToken") 