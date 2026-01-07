from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class TicketTypes(Base):
    __tablename__ = 'ticket_types'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)  # Keep index for FK queries
    name = Column(String)  # Removed index - not frequently queried
    description = Column(String)  # Removed index - not useful for description
    price = Column(Float)  # Removed index - rarely queried by exact price
    quantity = Column(Integer)  # Total quantity (for reference)
    available_quantity = Column(Integer, default=0)  # Tickets still available for purchase
    sold_quantity = Column(Integer, default=0)  # Tickets that have been sold

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Relationships
    event = relationship("Events", back_populates="ticket_types")
    tickets = relationship("Tickets", back_populates="ticket_type", cascade="all, delete-orphan")


class Tickets(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True)  # Keep index for FK queries
    ticket_type_id = Column(Integer, ForeignKey("ticket_types.id"), index=True)  # Keep index for FK queries
    seat_number = Column(String)  # Removed index - not frequently queried
    qr_code = Column(String, index=True, unique=True)  # Keep index for QR validation, add unique constraint
    qr_code_data = Column(String)  # JSON payload stored in QR code
    checked_in = Column(Boolean, default=False)
    checked_out = Column(Boolean, default=False)
    validated_at = Column(DateTime(timezone=True), nullable=True)  # When ticket was validated
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Staff member who validated

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Relationships
    order = relationship("Orders", back_populates="tickets")
    ticket_type = relationship("TicketTypes", back_populates="tickets")
