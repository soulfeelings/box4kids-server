from pydantic import BaseModel
from typing import List, Optional


class SaveCardTokenRequest(BaseModel):
    token: str


class SaveCardTokenResponse(BaseModel):
    success: bool
    error_message: Optional[str] = None


class ChargeRequest(BaseModel):
    subscription_ids: List[int]
    description: Optional[str] = ""


class ChargeResponse(BaseModel):
    success: bool
    receipt_id: Optional[str] = None
    status: Optional[str] = None
    payment_id: Optional[int] = None
    error_message: Optional[str] = None
