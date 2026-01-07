"""Authentication schemas for token management."""

from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: int  # User ID
    exp: int  # Expiration timestamp
    type: str  # Token type (access or refresh)


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing access token."""
    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Response schema for new access token."""
    access_token: str
    token_type: str = "bearer"
