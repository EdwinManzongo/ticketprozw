from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Keep index for FK and user queries
    event_id = Column(Integer, ForeignKey("events.id"), index=True)  # Keep index for FK and event queries
    order_date = Column(DateTime, index=True)  # Keep index for date range queries
    total_price = Column(Float)  # Removed index - rarely queried by exact price
    payment_method = Column(String)  # Removed index - not useful for queries
    payment_status = Column(String, index=True)  # Keep index for status filtering

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Relationships
    user = relationship("Users", back_populates="orders")
    event = relationship("Events", back_populates="orders")
    tickets = relationship("Tickets", back_populates="order", cascade="all, delete-orphan")
    payment_transaction = relationship("PaymentTransaction", back_populates="order", uselist=False, cascade="all, delete-orphan")

