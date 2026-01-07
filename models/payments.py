"""
Payment Transactions Model
"""
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class PaymentTransaction(Base):
    """Payment transaction model for tracking all payment activities"""
    __tablename__ = 'payment_transactions'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    status = Column(String(50), index=True)  # pending, succeeded, failed, cancelled
    payment_method = Column(String(50))  # card, bank_transfer, etc.

    # Stripe specific fields
    stripe_customer_id = Column(String(255))
    stripe_charge_id = Column(String(255))

    # Error tracking
    error_message = Column(String(500))

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    order = relationship("Orders", back_populates="payment_transaction")
