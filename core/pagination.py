"""
Pagination utilities for list endpoints
"""
from typing import TypeVar, Generic, List
from sqlalchemy.orm import Query
from pydantic import BaseModel


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True


def paginate(query: Query, skip: int = 0, limit: int = 20) -> dict:
    """
    Paginate a SQLAlchemy query

    Args:
        query: SQLAlchemy query object
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return

    Returns:
        Dictionary with pagination metadata and items
    """
    # Get total count
    total = query.count()

    # Get paginated items
    items = query.offset(skip).limit(limit).all()

    # Calculate pagination metadata
    has_next = (skip + limit) < total
    has_prev = skip > 0

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": has_next,
        "has_prev": has_prev
    }
