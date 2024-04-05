from pydantic import BaseModel


class TicketTypeBase(BaseModel):
    event_id: int
    name: str
    description: str
    price: float
    quantity: int


class TicketBase(BaseModel):
    order_id: int
    ticket_type_id: int
    seat_number: str
    qr_code: str
    checked_in: bool
    checked_out: bool


