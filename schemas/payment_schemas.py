from pydantic import BaseModel
from typing import List
from enum import Enum


class PaymentStatusEnum(str, Enum):
    """Статусы платежа"""
    SUCCESS = "success"
    FAILED = "failed"


class PaymentResult(BaseModel):
    """Схема результата обработки платежа"""
    status: PaymentStatusEnum
    message: str
    payment_id: int
    amount: float


class BatchPaymentCreateRequest(BaseModel):
    """Схема для создания пакетного платежа"""
    subscription_ids: List[int]


class BatchPaymentResponse(BaseModel):
    """Схема ответа при создании пакетного платежа"""
    payment_id: int
    external_payment_id: str
    payment_url: str
    amount: float
    currency: str
    subscription_count: int
    message: str


class ProcessPaymentResponse(BaseModel):
    """Схема ответа при обработке платежа"""
    status: str  # "success" или "failed"
    message: str


class PaymentReturnRequest(BaseModel):
    """Схема для возврата с платежной страницы"""
    external_payment_id: str
    status: str = "success"  # success или failed


class PaymentWebhookRequest(BaseModel):
    """Схема для webhook от платежной системы"""
    external_payment_id: str
    status: str  # succeeded, failed, refunded, pending


class ProcessSubscriptionsRequest(BaseModel):
    """Схема для обработки подписок"""
    subscription_ids: List[int]


class ProcessSubscriptionsResponse(BaseModel):
    """Схема ответа при обработке подписок"""
    status: PaymentStatusEnum
    message: str
    payment_id: int
    amount: float 