from __future__ import annotations
from datetime import datetime
import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class AuthUserBase(BaseModel):
    """Deprecated: Use /api/v1/auth/login endpoint instead."""
    username: str
    password: str


class UserBase(BaseModel):
    """User creation schema with password validation."""
    firstname: str = Field(..., min_length=1, max_length=100, description="User's first name")
    surname: str = Field(..., min_length=1, max_length=100, description="User's surname")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password")
    phone_number: str = Field(..., min_length=10, max_length=20, description="User's phone number")
    street_address: str = Field(..., min_length=5, max_length=200, description="User's street address")
    active: bool = True

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength.

        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')

        # Check for common weak passwords
        common_passwords = ['password', '12345678', 'qwerty', 'abc123', 'password123']
        if v.lower() in common_passwords:
            raise ValueError('Password is too common. Please choose a stronger password')

        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format (remove spaces and validate digits)."""
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s\-\(\)]', '', v)

        # Check if it contains only digits and optional + prefix
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValueError('Phone number must contain 10-15 digits')

        return v


class UserResponse(BaseModel):
    """User response schema - excludes sensitive data like password."""
    id: int
    firstname: str
    surname: str
    email: EmailStr
    phone_number: str
    street_address: str
    active: bool
    role: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """User update schema - all fields optional."""
    firstname: str | None = None
    surname: str | None = None
    phone_number: str | None = None
    street_address: str | None = None

