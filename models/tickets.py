from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from database import Base


class TicketTypes(Base):
    __tablename__ = 'ticket_types'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Float, index=True)
    quantity = Column(Integer, index=True)


class Tickets(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    ticket_type_id = Column(Integer, ForeignKey("ticket_types.id"))
    seat_number = Column(String, index=True)
    qr_code = Column(String, index=True)
    checked_in = Column(Boolean, default=False)
    checked_out = Column(Boolean, default=False)
