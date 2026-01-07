"""
Ticket validation schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TicketValidationRequest(BaseModel):
    """Schema for ticket validation request"""
    qr_code_data: str  # The QR code data string (JSON)
    event_id: int  # Event ID to validate against

    class Config:
        from_attributes = True


class TicketValidationResponse(BaseModel):
    """Schema for ticket validation response"""
    valid: bool
    message: str
    ticket_id: Optional[int] = None
    order_id: Optional[int] = None
    ticket_type: Optional[str] = None
    customer_name: Optional[str] = None
    already_checked_in: bool = False
    checked_in_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketCheckInRequest(BaseModel):
    """Schema for checking in a ticket"""
    ticket_id: int

    class Config:
        from_attributes = True


class TicketCheckInResponse(BaseModel):
    """Schema for ticket check-in response"""
    success: bool
    message: str
    ticket_id: int
    checked_in_at: datetime
    customer_name: str
    ticket_type: str
    seat_number: Optional[str] = None

    class Config:
        from_attributes = True


class TicketCheckOutRequest(BaseModel):
    """Schema for checking out a ticket"""
    ticket_id: int

    class Config:
        from_attributes = True


class TicketCheckOutResponse(BaseModel):
    """Schema for ticket check-out response"""
    success: bool
    message: str
    ticket_id: int
    checked_out_at: datetime

    class Config:
        from_attributes = True


class TicketStatusResponse(BaseModel):
    """Schema for ticket status"""
    ticket_id: int
    order_id: int
    event_id: int
    ticket_type: str
    seat_number: Optional[str] = None
    checked_in: bool
    checked_out: bool
    validated_at: Optional[datetime] = None
    validated_by: Optional[int] = None
    customer_name: str
    customer_email: str

    class Config:
        from_attributes = True
