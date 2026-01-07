from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String)
    surname = Column(String)
    email = Column(String, unique=True, index=True)  # Keep index on email for lookups
    password = Column(String)  # Removed index from password (security)
    phone_number = Column(String)
    street_address = Column(String)
    active = Column(Boolean, default=True)

    # New fields for authentication and role-based access
    role = Column(String, default="user")  # user, organizer, admin
    is_verified = Column(Boolean, default=False)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Relationships
    events = relationship("Events", back_populates="organizer", cascade="all, delete-orphan")
    orders = relationship("Orders", back_populates="user", cascade="all, delete-orphan")

