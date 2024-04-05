from pydantic import BaseModel
from datetime import datetime


class OrderBase(BaseModel):
    user_id: int
    event_id: int
    order_date: datetime
    total_price: float
    payment_method: str
    payment_status: str

