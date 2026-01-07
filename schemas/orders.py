from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method enum."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    CASH = "cash"


class OrderBase(BaseModel):
    """Order base schema with validation."""
    user_id: int = Field(..., gt=0, description="User ID")
    event_id: int = Field(..., gt=0, description="Event ID")
    order_date: datetime = Field(default_factory=datetime.utcnow, description="Order date")
    total_price: float = Field(..., ge=0, le=1000000, description="Total price in USD")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Payment status")

    @field_validator('total_price')
    @classmethod
    def validate_total_price(cls, v: float) -> float:
        """Validate total price is positive and reasonable."""
        if v < 0:
            raise ValueError('Total price cannot be negative')
        if v > 1000000:
            raise ValueError('Total price exceeds maximum allowed amount')
        # Round to 2 decimal places
        return round(v, 2)


class OrderCreate(BaseModel):
    """Order creation schema (user_id will be set from auth token)."""
    event_id: int = Field(..., gt=0)
    total_price: float = Field(..., ge=0, le=1000000)
    payment_method: PaymentMethod
    payment_status: PaymentStatus = PaymentStatus.PENDING

    @field_validator('total_price')
    @classmethod
    def validate_total_price(cls, v: float) -> float:
        """Validate and round total price."""
        if v < 0:
            raise ValueError('Total price cannot be negative')
        if v > 1000000:
            raise ValueError('Total price exceeds maximum allowed amount')
        return round(v, 2)


class OrderUpdate(BaseModel):
    """Order update schema - only payment status can be updated."""
    payment_status: PaymentStatus


class OrderResponse(BaseModel):
    """Order response schema."""
    id: int
    user_id: int
    event_id: int
    order_date: datetime
    total_price: float
    payment_method: str
    payment_status: str

    model_config = ConfigDict(from_attributes=True)

