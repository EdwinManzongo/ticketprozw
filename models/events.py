from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Events(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String)  # Removed index - full-text search will be used
    description = Column(String)  # Removed index - not useful for description
    organizer_id = Column(Integer, ForeignKey("users.id"), index=True)  # Keep index for FK lookups
    location = Column(String)  # Removed index - will add composite index if needed
    date = Column(DateTime, index=True)  # Keep index for date range queries
    image = Column(String)  # Removed index - not queried

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Relationships
    organizer = relationship("Users", back_populates="events")
    ticket_types = relationship("TicketTypes", back_populates="event", cascade="all, delete-orphan")
    orders = relationship("Orders", back_populates="event", cascade="all, delete-orphan")

