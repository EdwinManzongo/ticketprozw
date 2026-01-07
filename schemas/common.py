"""
Common schemas used across multiple resources
"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Query parameters for pagination"""
    skip: int = 0
    limit: int = 20

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str

    class Config:
        from_attributes = True
