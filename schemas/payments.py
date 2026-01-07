"""
Payment schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PaymentIntentCreate(BaseModel):
    """Schema for creating a payment intent"""
    order_id: int = Field(..., description="Order ID to create payment for")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", max_length=3, description="Currency code")

    class Config:
        from_attributes = True


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent response"""
    client_secret: str
    payment_intent_id: str
    amount: float
    currency: str
    status: str

    class Config:
        from_attributes = True


class PaymentTransactionResponse(BaseModel):
    """Schema for payment transaction response"""
    id: int
    order_id: int
    stripe_payment_intent_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    payment_method: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookEvent(BaseModel):
    """Schema for Stripe webhook event"""
    type: str
    data: dict

    class Config:
        from_attributes = True
