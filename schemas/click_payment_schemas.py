from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class PaymentType(str, Enum):
    SUBSCRIPTION = "subscription"


class CreateCardTokenRequest(BaseModel):
    card_number: str
    expire_date: str  # MMYY


class CreateCardTokenResponse(BaseModel):
    success: bool
    card_token_id: Optional[int] = None
    phone_number: Optional[str] = None
    error_message: Optional[str] = None


class VerifyCardTokenRequest(BaseModel):
    card_token_id: int
    sms_code: str


class VerifyCardTokenResponse(BaseModel):
    success: bool
    error_message: Optional[str] = None


class InitiatePaymentRequest(BaseModel):
    subscription_ids: List[int]
    card_token_id: int


class InitiatePaymentResponse(BaseModel):
    success: bool
    payment_id: Optional[int] = None
    click_payment_id: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    payment_id: int
    status: str
    amount: int
    created_at: str
    updated_at: str
    error_message: Optional[str] = None


class UserCardTokenResponse(BaseModel):
    id: int
    card_number: str
    expire_date: str
    is_verified: bool
    created_at: str
