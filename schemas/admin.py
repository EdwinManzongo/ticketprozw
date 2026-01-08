"""
Admin dashboard and analytics schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class SalesStatsResponse(BaseModel):
    """Sales statistics"""
    total_sales: float
    total_orders: int
    total_tickets_sold: int
    average_order_value: float
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EventStatsResponse(BaseModel):
    """Event statistics"""
    event_id: int
    event_name: str
    total_revenue: float
    total_orders: int
    total_tickets_sold: int
    available_tickets: int
    capacity_percentage: float

    model_config = ConfigDict(from_attributes=True)


class TopEventResponse(BaseModel):
    """Top performing events"""
    event_id: int
    event_name: str
    total_revenue: float
    total_tickets_sold: int

    model_config = ConfigDict(from_attributes=True)


class RevenueByEventResponse(BaseModel):
    """Revenue breakdown by event"""
    event_id: int
    event_name: str
    revenue: float
    percentage: float

    model_config = ConfigDict(from_attributes=True)


class UserActivityResponse(BaseModel):
    """User activity statistics"""
    total_users: int
    active_users: int
    new_users_this_month: int
    users_with_orders: int

    model_config = ConfigDict(from_attributes=True)


class PaymentMethodStatsResponse(BaseModel):
    """Payment method statistics"""
    payment_method: str
    count: int
    total_amount: float
    percentage: float

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """Complete dashboard with all analytics"""
    sales_stats: SalesStatsResponse
    user_activity: UserActivityResponse
    top_events: List[TopEventResponse]
    revenue_by_event: List[RevenueByEventResponse]
    payment_methods: List[PaymentMethodStatsResponse]
    total_revenue: float
    total_orders: int
    total_tickets_sold: int

    model_config = ConfigDict(from_attributes=True)


class TicketTransferRequest(BaseModel):
    """Request to transfer a ticket"""
    ticket_id: int
    new_owner_email: str
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TicketTransferResponse(BaseModel):
    """Response after ticket transfer"""
    ticket_id: int
    old_owner_id: int
    new_owner_id: int
    transferred_at: datetime
    message: str

    model_config = ConfigDict(from_attributes=True)
